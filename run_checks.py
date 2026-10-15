# -*- coding: utf-8 -*-
"""Checks of the simulator.  Run:  python run_checks.py

Every check prints PASS or FAIL with the numbers it compared; the same text is
written to ``checks_report.txt``.  The exit code is the number of failed checks.

1  geometry            site placement, line of sight (hand cases), map lookup, trajectories
2  path loss           TR 38.901 formulas against values computed by hand
3  radio statistics    shadowing field, time-varying part, L3 filter, in-street LOS share
4  determinism         same seed -> identical events; other seed -> different events
5  conservation        every attempt has one outcome, every failure one cause, preparations add up
6  equivalences        zero-weight rules equal their plain counterparts; conditional handover with
                       immediate execution equals the baseline handover
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from bh6.backend import NumpyOps
from bh6.layout import grid_layout, open_layout, los_matrix
from bh6.params import Scenario, Radio
from bh6.pathloss import (pl_umi_los, pl_umi_nlos, pl_uma_los, pl_uma_nlos, p_los_umi, breakpoint_distance, path_loss)
from bh6.radio import RadioMap, RadioSource
from bh6.sim import build_world, run_rules

LINES, FAILED = [], [0]


def say(msg=""):
    print(msg)
    LINES.append(msg)


def check(name, ok, detail=""):
    say("%s  %s%s" % ("PASS" if ok else "FAIL", name, ("  [" + detail + "]") if detail else ""))
    if not ok:
        FAILED[0] += 1


def rows(eng):
    """Event rows without the columns that legitimately differ between equivalent rules."""
    return [(r[1], r[2], r[3], r[5], r[6], r[7]) for r in eng.log]      # t_exec, t_end, ue, src, tgt, outcome


# ---------------------------------------------------------------------------
def geometry():
    say("\n== 1 geometry ==")
    for isd, n_exp in ((50.0, None), (100.0, None), (150.0, None)):
        L = grid_layout(isd)
        d = np.hypot(L.sites[:, None, 0] - L.sites[None, :, 0], L.sites[:, None, 1] - L.sites[None, :, 1])
        np.fill_diagonal(d, 1e9)
        in_street = L.street_mask(L.sites[:, 0], L.sites[:, 1]).all()
        check("grid isd %g: %d sites, all in a street, nearest neighbours %.1f..%.1f m" %
              (isd, L.M, d.min(1).min(), d.min(1).max()), in_street and d.min() >= 0.4 * isd - 1e-6)
    L = grid_layout(100.0)
    say("    building blocks: %s" % L.buildings.tolist())
    site = np.array([[0.0, 9.0]])
    pts = np.array([[200.0, 0.0],      # same street                          -> LOS
                    [433.0, 0.0],      # intersection at the end of the street -> LOS
                    [433.0, 100.0],    # round the corner                      -> blocked
                    [0.0, -200.0],     # crossing street through the site's intersection -> LOS
                    [-433.0, -250.0],  # opposite corner of the area           -> blocked
                    [5.0, 240.0]])     # crossing street x = 0, 5 m off the centre line -> LOS
    exp = np.array([True, True, False, True, False, True])
    got = los_matrix(pts[:, 0], pts[:, 1], site, L.buildings)[:, 0]
    check("line of sight, six hand cases", bool((got == exp).all()), "got %s" % got.astype(int).tolist())
    # a ray that only touches the corner (10, 10) of a block is clear; one that cuts 1 m into the block is blocked
    touch = los_matrix(np.array([20.0]), np.array([0.0]), np.array([[0.0, 20.0]]), L.buildings)[0, 0]
    cut = los_matrix(np.array([22.0]), np.array([0.0]), np.array([[0.0, 22.0]]), L.buildings)[0, 0]
    check("ray touching a building corner is clear, ray cutting the corner is blocked", bool(touch) and not bool(cut))
    Lo = open_layout(100.0)
    d = np.hypot(Lo.sites[:, None, 0] - Lo.sites[None, :, 0], Lo.sites[:, None, 1] - Lo.sites[None, :, 1])
    np.fill_diagonal(d, 1e9)
    check("open area: hexagonal grid, nearest-neighbour distance = isd", abs(np.median(d.min(1)) - 100.0) < 1e-6,
          "%d sites" % Lo.M)
    # map lookup against a direct computation (no shadowing, no clutter)
    sc = Scenario(isd=100.0, clutter=False).with_(radio__place_share=0.0)
    rm = RadioMap(L, sc.radio, 1, NumpyOps(), clutter=False)
    rng = np.random.default_rng(5)
    x = rng.uniform(-430, 430, 400)
    y = np.zeros(400) + rng.uniform(-4, 4, 400)
    d2 = np.hypot(x[:, None] - L.sites[None, :, 0], y[:, None] - L.sites[None, :, 1])
    los = los_matrix(x, y, L.sites, L.buildings)
    direct = -path_loss(d2, los, sc.radio)
    got = rm.lookup(x, y)
    near = np.abs(los_matrix(x + 1.0, y, L.sites, L.buildings) ^ los_matrix(x - 1.0, y, L.sites, L.buildings)) | \
        np.abs(los_matrix(x, y + 1.0, L.sites, L.buildings) ^ los_matrix(x, y - 1.0, L.sites, L.buildings))
    err = np.abs(got - direct)[~near & (d2 > 15.0)]
    check("radio-map lookup = direct path loss away from LOS edges", err.max() < 0.05, "max |diff| %.4f dB" % err.max())
    # trajectories
    for prof in ("veh16", "ped"):
        sc = Scenario(isd=100.0, profile=prof, t_sim=300.0, n_ue=80, seed=4)
        w = build_world(sc)
        X, Y, V, TH = w.traj
        step = np.hypot(np.diff(X, axis=0), np.diff(Y, axis=0))
        ok_speed = np.allclose(step.max(0), V * sc.proto.dt, rtol=1e-6, atol=1e-9)
        ok_street = w.layout.street_mask(X, Y).all()
        check("trajectories (%s): constant speed, always inside a street" % prof, ok_speed and bool(ok_street),
              "speeds %.1f..%.1f m/s" % (V.min(), V.max()))
    # turn statistics at the central four-way intersection
    sc = Scenario(isd=100.0, profile="veh30", t_sim=1500.0, n_ue=150, seed=9)
    from bh6.mobility import gen_traj
    X, Y, V, TH = gen_traj(L, sc, np.random.default_rng(1))
    n_s = n_t = 0
    for u in range(X.shape[1]):
        inside = (np.abs(X[:, u]) < 12) & (np.abs(Y[:, u]) < 12)
        enter = np.nonzero(inside[1:] & ~inside[:-1])[0]
        for e in enter:
            out = e + 1
            while out < len(inside) and inside[out]:
                out += 1
            if out < len(inside) and e > 0:
                same = abs(math.remainder(float(TH[out, u]) - float(TH[e - 1, u]), 2 * math.pi)) < 0.1
                n_s += same
                n_t += not same
    frac = n_s / max(n_s + n_t, 1)
    check("turns at the four-way intersection: straight 0.5", abs(frac - 0.5) < 0.06, "%d passes, straight %.3f" % (n_s + n_t, frac))


# ---------------------------------------------------------------------------
def pathloss_checks():
    say("\n== 2 path loss (TR 38.901 Table 7.4.1-1), computed by hand ==")
    # hand values (derivation in PLAN.md, section "Checks"); c = 299 792 458 m/s
    cases = [
        ("UMi LOS  10 GHz d2D 50 m  hBS 10 hUT 1.5 (PL1)", float(pl_umi_los(np.array(50.0), 10.0, 10.0, 1.5)), 88.2083),
        ("UMi NLOS 10 GHz d2D 50 m", float(pl_umi_nlos(np.array(50.0), 10.0, 10.0, 1.5)), 103.8920),
        ("UMi LOS  3.5 GHz d2D 200 m (PL1, below d'BP 210.1 m)", float(pl_umi_los(np.array(200.0), 3.5, 10.0, 1.5)), 91.6112),
        ("UMi LOS  3.5 GHz d2D 400 m (PL2, above d'BP)", float(pl_umi_los(np.array(400.0), 3.5, 10.0, 1.5)), 103.2331),
        ("UMa LOS  3.5 GHz d2D 100 m hBS 25", float(pl_uma_los(np.array(100.0), 3.5, 25.0, 1.5)), 83.1382),
        ("UMa NLOS 3.5 GHz d2D 100 m hBS 25", float(pl_uma_nlos(np.array(100.0), 3.5, 25.0, 1.5)), 103.0376),
        ("breakpoint d'BP 10 GHz hBS 10 hUT 1.5 [m]", breakpoint_distance(10.0, 10.0, 1.5), 600.415),
        ("breakpoint d'BP 3.5 GHz [m]", breakpoint_distance(3.5, 10.0, 1.5), 210.145),
        ("UMi LOS probability at 100 m", float(p_los_umi(100.0)), 0.230985),
    ]
    for name, got, hand in cases:
        tol = 0.005 if hand > 1 else 5e-6
        check(name, abs(got - hand) < tol, "code %.4f, hand %.4f" % (got, hand))
    # continuity at the breakpoint and NLOS >= LOS
    dbp = breakpoint_distance(10.0, 10.0, 1.5)
    a = float(pl_umi_los(np.array(dbp - 1e-6), 10.0)); b = float(pl_umi_los(np.array(dbp + 1e-6), 10.0))
    check("UMi LOS continuous at the breakpoint", abs(a - b) < 1e-3, "%.4f / %.4f dB" % (a, b))
    d = np.linspace(10, 2000, 500)
    check("NLOS loss >= LOS loss everywhere (UMi 7, 10, 15 GHz; UMa 3.5 GHz)",
          all((pl_umi_nlos(d, f) >= pl_umi_los(d, f) - 1e-9).all() for f in (7.0, 10.0, 15.0))
          and bool((pl_uma_nlos(d, 3.5) >= pl_uma_los(d, 3.5) - 1e-9).all()))
    R = Radio()
    check("noise power 200 MHz, NF 7 dB", abs(R.noise_dbm - (-174 + 83.0103 + 7)) < 1e-3, "%.3f dBm" % R.noise_dbm)


# ---------------------------------------------------------------------------
def radio_stats():
    say("\n== 3 radio statistics ==")
    L = grid_layout(100.0)
    sc = Scenario(isd=100.0)
    rm0 = RadioMap(L, sc.with_(radio__place_share=0.0).radio, 3, NumpyOps(), clutter=False)
    rm1 = RadioMap(L, sc.radio, 3, NumpyOps(), clutter=False)
    f = (rm1.gain[:-1] - rm0.gain[:-1])            # the static field x sigma
    los = rm1.los[:-1]
    check("static shadowing: std %.2f dB on LOS links (4.0), %.2f dB on NLOS links (7.82)" %
          (f[los].std(), f[~los].std()), abs(f[los].std() - 4.0) < 0.4 and abs(f[~los].std() - 7.82) < 0.8)
    # spatial correlation along the middle street
    xs = np.arange(-400.0, 400.0, 1.0)
    z = (rm1.lookup(xs, np.zeros_like(xs)) - rm0.lookup(xs, np.zeros_like(xs)))
    lz = rm1.los_at(xs, np.zeros_like(xs))
    z = z / np.where(lz, 4.0, 7.82)

    def corr(lag):
        a, b = z[:-lag], z[lag:]
        return float(np.mean([np.corrcoef(a[:, m], b[:, m])[0, 1] for m in range(z.shape[1])]))
    c10, c20 = corr(10), corr(20)
    check("static shadowing: correlation %.2f at 10 m (1/e = 0.37), %.2f at 20 m" % (c10, c20),
          abs(c10 - 0.37) < 0.12 and c20 < 0.15)
    cc = np.corrcoef((f / np.where(los, 4.0, 7.82)).T)
    off = cc[~np.eye(len(cc), dtype=bool)].mean()
    check("static shadowing: correlation between sites %.2f (0.5)" % off, abs(off - 0.5) < 0.15)
    # in-street LOS share with clutter against the TR 38.901 probability
    rmc = RadioMap(L, sc.radio, 3, NumpyOps(), clutter=True)
    geo = rm1.los[:-1]
    ys_, xs_ = np.nonzero(rmc.idx < rmc.n_pix)
    px = rmc.x0 + xs_ * rmc.res; py = rmc.y0 + ys_ * rmc.res
    order = rmc.idx[ys_, xs_]
    d2 = np.empty((rmc.n_pix, L.M)); d2[order] = np.hypot(px[:, None] - L.sites[None, :, 0], py[:, None] - L.sites[None, :, 1])
    ok = True
    txt = []
    for lo, hi in ((20, 40), (40, 80), (80, 160), (160, 320)):
        sel = geo & (d2 >= lo) & (d2 < hi)
        got = rmc.los[:-1][sel].mean(); exp = p_los_umi(d2[sel]).mean()
        txt.append("%d-%d m: %.2f (%.2f)" % (lo, hi, got, exp))
        ok &= abs(got - exp) < 0.08
    check("clutter: share of unobstructed in-street links follows the UMi LOS probability", ok, "; ".join(txt))
    # time-varying part and measurement noise
    sc2 = Scenario(isd=100.0, t_sim=60.0, n_ue=30, seed=2)
    w = build_world(sc2)
    src = RadioSource(w.rmap, w.traj, sc2)
    src_q = RadioSource(w.rmap, w.traj, sc2.with_(radio__sigma_t=0.0, radio__meas_sigma=0.0))
    d, n1 = [], []
    for ch, cq in zip(src.chunks(), src_q.chunks()):
        d.append((ch.rsrp - cq.rsrp)[::ch.mp]); n1.append(ch.l1 - ch.rsrp[::ch.mp])
    d = np.concatenate(d); n1 = np.concatenate(n1)
    r = float(np.mean(d[:-25] * d[25:]) / d.var())
    check("time-varying part: std %.2f dB (1.5), correlation after 1 s %.2f (0.37)" % (d.std(), r),
          abs(d.std() - 1.5) < 0.1 and abs(r - 0.37) < 0.06)
    check("L1 sample error: std %.2f dB (1.0), mean %.3f" % (n1.std(), n1.mean()), abs(n1.std() - 1.0) < 0.02 and abs(n1.mean()) < 0.01)
    from bh6.engine import Engine
    from bh6.policies import A3
    e = Engine(sc2, w.layout, w.rmap, w.traj, w.svc, w.bg, A3())
    e200 = Engine(sc2.with_(proto__meas_period=0.2), w.layout, w.rmap, w.traj, w.svc, w.bg, A3())
    check("L3 filter: a = 0.5 at 200 ms (k = 4); 5 samples of 40 ms have the same effect",
          abs(e200.a3 - 0.5) < 1e-12 and abs((1 - e.a3) ** 5 - 0.5) < 1e-12, "a(40 ms) = %.4f" % e.a3)


# ---------------------------------------------------------------------------
SPECS = [dict(rule="a3", off=3.0, ttt=0.16, name="A3"),
         dict(rule="a3", off=6.0, ttt=0.32, name="A3 late"),
         dict(rule="pum", h0=2.0, ttt=0.16, eta_h=8, eta_l=4, eta_a=4, name="PUM"),
         dict(rule="cho", o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, n_max=4, name="CHO"),
         dict(rule="cho", o_prep=0.0, o_exec=8.0, ttt_exec=0.32, n_max=2, name="CHO late"),
         dict(rule="memcho", o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, n_max=4, w_u=8, w_l=8, w_a=2, v_u=4, v_l=4, v_a=2,
              name="MemCHO")]


def determinism_conservation():
    say("\n== 4 determinism ==")
    sc = Scenario(isd=100.0, profile="veh16", t_sim=150.0, discard=0.0, seed=11).with_(radio__chi=1.0)
    r1, e1 = run_rules(sc, SPECS, log_events=True)
    r2, e2 = run_rules(sc, SPECS, log_events=True)
    same = all(a.log == b.log for a, b in zip(e1, e2)) and all(
        {k: v for k, v in a.items() if k != "wall_s"} == {k: v for k, v in b.items() if k != "wall_s"} for a, b in zip(r1, r2))
    check("same seed twice: identical event logs and metrics for all %d rules" % len(SPECS), same,
          "events per rule: %s" % [len(e.log) for e in e1])
    r3, e3 = run_rules(sc.with_(seed=12), SPECS[:1], log_events=True)
    check("another seed: different events", e3[0].log != e1[0].log, "%d vs %d events" % (len(e3[0].log), len(e1[0].log)))

    say("\n== 5 conservation (strong interference, chi = 1, so that many failures occur) ==")
    for r, e in zip(r1, e1):
        n_out = sum(r["n_" + k] for k in ("useful", "unnecessary", "early", "wrong", "late", "censored"))
        n_cause = sum(r["c_f_" + k] for k in ("late_cmd", "late_prep", "late_rlf", "cov_rlf", "exec_fail", "early_rlf"))
        ok = n_out == r["c_att"] == e.C["att_all"] and n_cause == r["c_fail"]
        n_log_att = sum(1 for x in e.log if x[4] != "rlf")
        n_log_rlf = sum(1 for x in e.log if x[4] == "rlf")
        ok &= n_log_att == r["c_att"] and n_log_rlf == r["c_f_late_rlf"] + r["c_f_cov_rlf"]
        ok &= r["n_early"] + r["n_wrong"] == r["c_f_exec_fail"] + r["c_f_early_rlf"]
        detail = "attempts %d = useful %d + unnecessary %d + early %d + wrong %d + late %d + censored %d; failures %d" % (
            r["c_att"], r["n_useful"], r["n_unnecessary"], r["n_early"], r["n_wrong"], r["n_late"], r["n_censored"], r["c_fail"])
        if r["kind"] == "cho":
            okp = r["c_prep_req"] == r["c_cfg_lost"] + r["c_prep_cancel"] + r["c_prep_used"] + r["c_prep_wasted"] + r["prep_left"]
            ok &= okp
            detail += "; preparations %d = lost %d + cancelled %d + used %d + unused %d + open %d" % (
                r["c_prep_req"], r["c_cfg_lost"], r["c_prep_cancel"], r["c_prep_used"], r["c_prep_wasted"], r["prep_left"])
        check("%-9s counts add up" % r["rule"], bool(ok), detail)
    tot = {k: sum(r["c_f_" + k] for r in r1) for k in ("late_cmd", "late_prep", "late_rlf", "cov_rlf", "exec_fail", "early_rlf")}
    say("    failure causes seen in this check (all rules): %s" % tot)
    return sc


def equivalences(sc):
    say("\n== 6 equivalences ==")
    # (a) per-user margin with zero weights = A3
    res, eng = run_rules(sc, [dict(rule="a3", off=2.0, ttt=0.16, name="A3"),
                              dict(rule="pum", h0=2.0, ttt=0.16, eta_h=0, eta_l=0, eta_a=0, eta_s=0, name="PUM0")], log_events=True)
    check("per-user margin with zero weights = A3", eng[0].log == eng[1].log, "%d events" % len(eng[0].log))
    # (b) memory-steered conditional handover with zero weights = conditional handover
    c = dict(o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, n_max=3, rel_hys=3.0)
    res, eng = run_rules(sc, [dict(rule="cho", name="CHO", **c), dict(rule="memcho", name="M0", **c),
                              dict(rule="memcho", name="M1", w_u=8, w_l=8, v_u=4, v_a=2, **c)], log_events=True)
    k = [x for x in res[0] if x not in ("rule", "wall_s")]
    check("memory-steered CHO with zero weights = CHO (events and all metrics)",
          eng[0].log == eng[1].log and all(res[0][x] == res[1][x] for x in k), "%d events" % len(eng[0].log))
    check("... and with non-zero weights it differs", eng[2].log != eng[0].log)
    # (c) conditional handover with immediate execution = baseline handover
    sce = sc.with_(proto__report_interval=sc.proto.meas_period, proto__cfg_loss_as_hof=True)
    for off, ttt in ((3.0, 0.16), (1.0, 0.04), (6.0, 0.32)):
        res, eng = run_rules(sce, [dict(rule="a3", off=off, ttt=ttt, name="A3"),
                                   dict(rule="cho", o_prep=off, ttt_prep=ttt, immediate=True, n_max=1, rel_hys=1e9, name="CHOi")],
                             log_events=True)
        a, b = rows(eng[0]), rows(eng[1])
        same = a == b and all(res[0][x] == res[1][x] for x in ("c_ho", "c_fail", "n_useful", "n_unnecessary", "n_early",
                                                               "n_wrong", "n_late", "c_f_late_cmd", "c_f_exec_fail"))
        check("CHO with immediate execution = A3 (%g dB, %g ms)" % (off, ttt * 1000), same,
              "%d / %d events, failures %d / %d" % (len(a), len(b), res[0]["c_fail"], res[1]["c_fail"]))
    # (d) what the 'lost configuration = lost command' switch is needed for
    res, eng = run_rules(sc.with_(proto__report_interval=sc.proto.meas_period),
                         [dict(rule="a3", off=6.0, ttt=0.32, name="A3"),
                          dict(rule="cho", o_prep=6.0, ttt_prep=0.32, immediate=True, n_max=1, rel_hys=1e9, name="CHOi")],
                         log_events=True)
    a, b = set(rows(eng[0])), set(rows(eng[1]))
    say("    without that switch a lost configuration is not a handover failure: %d of %d events differ "
        "(%d lost configurations); this difference is intended" % (len(a ^ b), len(a | b), res[1]["c_cfg_lost"]))


if __name__ == "__main__":
    geometry()
    pathloss_checks()
    radio_stats()
    sc = determinism_conservation()
    equivalences(sc)
    say("\n%d check(s) failed" % FAILED[0])
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "checks_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    sys.exit(FAILED[0])
