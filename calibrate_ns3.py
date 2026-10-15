# -*- coding: utf-8 -*-
"""Calibration against the group's ns-3 / 5G-LENA study (3.5 GHz, same street-grid layout).

Reference: ``ns3_reference/campaign_urban_results.csv`` (read only): stock
Event A3 in the TR 37.885 urban grid with seven sites, 20 vehicles, 3.5 GHz.

  part A  the 24 A3 settings (offset 1/2/3/6 dB x TTT 100/300/500 ms ... as in the file)
          on the four validation conditions (site distance 400/200 m, 16/30 m/s),
          150 s runs with the first 60 s discarded
  part B  the two A3 settings of the test phase on the six conditions
          (site distance 400/200 m x 8/16/30 m/s), 180 s runs, 60 s discarded

This simulator is set to the same scenario: same sites, 10 m height, 40 dBm,
omni-directional antennas (no beam gain, no isolation), 10 MHz, UMi street
canyon, line of sight from the building geometry only (no clutter), shadowing
as a process along each user's path (ns-3 draws it per link), constant speeds
on the street centre lines, one L1 sample every 200 ms, light traffic.  Seeds
are different realisations, so only averages can be compared.

Run:  python calibrate_ns3.py [--workers N] [--seeds K] [--ref PATH]
Writes ``calibration_report.txt`` and ``calibration.json``.
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

from bh6.params import Scenario, Radio, Proto, Load
from bh6.sim import run_rules

REF = os.path.join(HERE, "ns3_reference", "campaign_urban_results.csv")   # ns-3 / 5G-LENA runs of the urban scenario
SITES = {400: ((0, 0), (400, 0), (-400, 0), (200, 250), (-200, 250), (200, -250), (-200, -250)),
         200: ((0, 0), (200, 0), (-200, 0), (100, 250), (-100, 250), (100, -250), (-100, -250))}
LIGHT_LOAD = 0.03        # share of slots in which a cell transmits at 10 packets/s per UE (assumption, see report)


def scenario(isd, speed, seed, t_sim, load=LIGHT_LOAD):
    """The ns-3 urban scenario expressed in this simulator's parameters."""
    radio = Radio(fc_ghz=3.5, bw_hz=10e6, tx_dbm=40.0, g_bs_db=0.0, nf_db=5.0, chi=1.0, place_share=0.0,
                  sigma_t=0.0, meas_sigma=0.0, d_corr=10.0)
    proto = Proto(meas_period=0.2, report_interval=0.2, lab_period=0.2, t_exec=0.01)
    ld = Load(hot_frac=0.0, bg_norm=(load, load), bg_hot=(load, load), rate_scale=0.001)
    return Scenario(name="ns3-urban", env="grid", isd=float(isd), profile="c%d" % speed, n_ue=20, t_sim=t_sim,
                    discard=60.0, seed=seed, sites=SITES[isd], clutter=False, radio=radio, proto=proto, load=ld)


def job(a):
    isd, speed, seed, t_sim, cfgs, load = a
    specs = [dict(rule="a3", off=float(h), ttt=t / 1000.0, name="A3_h%g_t%d" % (h, t)) for h, t in cfgs]
    res, _ = run_rules(scenario(isd, speed, seed, t_sim, load), specs)
    return [(isd, speed, seed, h, t, r["att_pm"], r["uho_pm"], r["fail_pm"], r["sinr_db"], r["late_pm"], r["pp_pm"])
            for (h, t), r in zip(cfgs, res)]


def read_ref(path):
    tune, test = defaultdict(list), defaultdict(list)
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["rule"] != "a3":
                continue
            v = (float(r["ho_pm"]), float(r["uho_pm"]), float(r["fail_pm"]), float(r["sinr_db"]))
            key = (int(float(r["isd"])), int(float(r["speed"])), float(r["hyst"]), int(float(r["ttt_ms"])))
            (tune if r["phase"] == "tune" else test if r["phase"] == "test" else defaultdict(list))[key].append(v)
    return tune, test


def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--ref", default=REF)
    a = ap.parse_args()
    tune, test = read_ref(a.ref)
    cfgs = sorted({(k[2], k[3]) for k in tune})
    cells_a = sorted({(k[0], k[1]) for k in tune})
    cfgs_b = sorted({(k[2], k[3]) for k in test})
    cells_b = sorted({(k[0], k[1]) for k in test})
    jobs = [(i, v, 500 + s, 150.0, cfgs, LIGHT_LOAD) for (i, v) in cells_a for s in range(a.seeds)]
    jobs += [(i, v, 600 + s, 180.0, cfgs_b, LIGHT_LOAD) for (i, v) in cells_b for s in range(a.seeds)]
    # the failure detector depends on the interference actually present: bracket the load assumption
    jobs += [(i, v, 500 + s, 150.0, cfgs, ld) for (i, v) in cells_a for s in range(a.seeds) for ld in (0.0, 0.10)]
    from concurrent.futures import ProcessPoolExecutor
    out = []
    with ProcessPoolExecutor(a.workers) as ex:
        for n, rows in enumerate(ex.map(job, jobs)):
            out.append((jobs[n], rows))
            print("job %d/%d done" % (n + 1, len(jobs)), flush=True)

    def mine(t_sim, load):
        d = defaultdict(list)
        for j, rows in out:
            if j[3] == t_sim and j[5] == load:
                for (isd, v, seed, h, t, ho, uho, fail, sinr, late, pp) in rows:
                    d[(isd, v, h, t)].append((ho, uho, fail, sinr))
        return d

    L = []
    w = L.append
    w("Calibration against ns-3 / 5G-LENA (campaign_urban, stock Event A3, 3.5 GHz, TR 37.885 grid, 7 sites, 20 UEs)")
    w("ns-3: one run per condition and setting in part A (seeds 101-104), 20 seeds in part B.")
    w("This simulator: %d seeds per condition; background load %.2f (assumption for 10 packets/s per UE)." % (a.seeds, LIGHT_LOAD))
    w("Rates per UE-minute.  HO = handover attempts, UHO = unnecessary handovers, F = mobility failures.")
    w("")
    w("Part A: 24 settings, mean over the four validation conditions")
    w("%-14s | %7s %7s %6s | %7s %7s %6s | %6s %6s" % ("setting", "ns3 HO", "ns3 UHO", "ns3 F", "sim HO", "sim UHO", "sim F", "HO x", "UHO x"))
    m = mine(150.0, LIGHT_LOAD)
    A = []
    for (h, t) in cfgs:
        ref = np.mean([np.mean(tune[(i, v, h, t)], axis=0) for (i, v) in cells_a], axis=0)
        sim = np.mean([np.mean(m[(i, v, h, t)], axis=0) for (i, v) in cells_a], axis=0)
        A.append((h, t, ref, sim))
        w("%4g dB %4d ms | %7.2f %7.2f %6.3f | %7.2f %7.2f %6.3f | %6.2f %6.2f" %
          (h, t, ref[0], ref[1], ref[2], sim[0], sim[1], sim[2], sim[0] / ref[0], sim[1] / max(ref[1], 1e-9)))
    rh = np.array([x[2][0] for x in A]); sh = np.array([x[3][0] for x in A])
    ru = np.array([x[2][1] for x in A]); su = np.array([x[3][1] for x in A])
    rf = np.array([x[2][2] for x in A]); sf = np.array([x[3][2] for x in A])
    summ = dict(
        ho_ratio_median=float(np.median(sh / rh)), ho_ratio_min=float((sh / rh).min()), ho_ratio_max=float((sh / rh).max()),
        uho_ratio_median=float(np.median(su / np.maximum(ru, 1e-9))), uho_ratio_min=float((su / np.maximum(ru, 1e-9)).min()),
        uho_ratio_max=float((su / np.maximum(ru, 1e-9)).max()),
        ho_spearman=spearman(rh, sh), uho_spearman=spearman(ru, su), fail_spearman=spearman(rf, sf),
        ho_mean_ns3=float(rh.mean()), ho_mean_sim=float(sh.mean()), uho_mean_ns3=float(ru.mean()), uho_mean_sim=float(su.mean()),
        fail_mean_ns3=float(rf.mean()), fail_mean_sim=float(sf.mean()),
        uhr_ns3=float((ru / rh).mean()), uhr_sim=float((su / sh).mean()))
    w("")
    w("Summary A: HO ratio sim/ns-3 median %.2f (range %.2f-%.2f); UHO ratio median %.2f (range %.2f-%.2f)" %
      (summ["ho_ratio_median"], summ["ho_ratio_min"], summ["ho_ratio_max"], summ["uho_ratio_median"], summ["uho_ratio_min"], summ["uho_ratio_max"]))
    w("           rank correlation over the 24 settings: HO %.2f, UHO %.2f, failures %.2f" %
      (summ["ho_spearman"], summ["uho_spearman"], summ["fail_spearman"]))
    w("           mean over settings: HO %.2f (ns-3) / %.2f (sim); UHO %.2f / %.2f; failures %.3f / %.3f; unnecessary share %.2f / %.2f" %
      (summ["ho_mean_ns3"], summ["ho_mean_sim"], summ["uho_mean_ns3"], summ["uho_mean_sim"], summ["fail_mean_ns3"],
       summ["fail_mean_sim"], summ["uhr_ns3"], summ["uhr_sim"]))
    w("")
    w("Failures against the load assumed for the interfering cells (mean over the 24 settings):")
    for ld in (0.0, LIGHT_LOAD, 0.10):
        mm = mine(150.0, ld)
        f = np.mean([np.mean([np.mean(mm[(i, v, h, t)], axis=0)[2] for (i, v) in cells_a]) for (h, t) in cfgs])
        s = np.mean([np.mean([np.mean(mm[(i, v, h, t)], axis=0)[3] for (i, v) in cells_a]) for (h, t) in cfgs])
        w("   load %.2f: failures %.3f per UE-minute, mean serving SINR %.1f dB   (ns-3: %.3f, %.1f dB)" %
          (ld, f, s, rf.mean(), np.mean([x[2][3] for x in A])))
    w("")
    w("Part A by condition (mean over the 24 settings)")
    for (i, v) in cells_a:
        ref = np.mean([np.mean(tune[(i, v, h, t)], axis=0) for (h, t) in cfgs], axis=0)
        sim = np.mean([np.mean(m[(i, v, h, t)], axis=0) for (h, t) in cfgs], axis=0)
        w("   site distance %d m, %2d m/s: HO %.2f / %.2f, UHO %.2f / %.2f, failures %.3f / %.3f, SINR %.1f / %.1f dB  (ns-3 / sim)" %
          (i, v, ref[0], sim[0], ref[1], sim[1], ref[2], sim[2], ref[3], sim[3]))
    w("")
    w("Part B: test-phase settings, six conditions (ns-3: 20 seeds each)")
    mb = mine(180.0, LIGHT_LOAD)
    B = []
    for (h, t) in cfgs_b:
        for (i, v) in cells_b:
            if (i, v, h, t) not in test:
                continue
            ref = np.mean(test[(i, v, h, t)], axis=0); rsd = np.std(test[(i, v, h, t)], axis=0, ddof=1)
            sim = np.mean(mb[(i, v, h, t)], axis=0)
            B.append(dict(hyst=h, ttt=t, isd=i, speed=v, ns3=ref.tolist(), sim=sim.tolist()))
            w("   %g dB / %d ms, %d m, %2d m/s: HO %.2f (sd %.2f) / %.2f, UHO %.2f (sd %.2f) / %.2f, failures %.3f / %.3f" %
              (h, t, i, v, ref[0], rsd[0], sim[0], ref[1], rsd[1], sim[1], ref[2], sim[2]))
    hb = np.array([[b["ns3"][0], b["sim"][0], b["ns3"][1], b["sim"][1]] for b in B])
    summ["partB_ho_ratio_median"] = float(np.median(hb[:, 1] / hb[:, 0]))
    summ["partB_uho_ratio_median"] = float(np.median(hb[:, 3] / np.maximum(hb[:, 2], 1e-9)))
    w("Summary B: HO ratio median %.2f, UHO ratio median %.2f" % (summ["partB_ho_ratio_median"], summ["partB_uho_ratio_median"]))
    txt = "\n".join(L) + "\n"
    print(txt)
    with open(os.path.join(HERE, "calibration_report.txt"), "w", encoding="utf-8") as f:
        f.write(txt)
    with open(os.path.join(HERE, "calibration.json"), "w", encoding="utf-8") as f:
        json.dump(dict(summary=summ, partA=[dict(hyst=h, ttt=t, ns3=r.tolist(), sim=s.tolist()) for h, t, r, s in A], partB=B), f, indent=1)


if __name__ == "__main__":
    main()
