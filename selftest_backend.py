# -*- coding: utf-8 -*-
"""Self-test of the computing back-ends on this machine.  Run once before the study:

    python selftest_backend.py

What it does
  1. Correctness.  The radio map and the radio samples are computed with NumPy
     (reference) and, if PyTorch is installed, with PyTorch on the CPU and on
     the GPU.  The largest difference in dB is printed, and one short
     simulation is run per back-end; its event logs must be identical to the
     reference.
  2. Speed of one process: seconds for the radio map and for the map lookups.
  3. Speed of the real workload: the same small batch of jobs is run through
     the worker pool once per back-end, and the jobs per minute are compared.
     This is the number that matters, because the study runs many processes
     at once and they would all share one GPU.

Result: ``backend_choice.json`` with the fastest back-end that reproduced the
reference exactly in step 1 (otherwise "cpu"), and ``selftest_report.txt``.
``run_all.py --device auto`` (the default) reads that file.  Nothing is
assumed about the GPU: if it is not faster for this workload, it is not used.

Where a GPU can help here at all: only the deterministic radio computations
(line-of-sight geometry, path loss, map interpolation) go through the
back-end.  The protocol engine, which takes most of the time, runs on the CPU
in any case, and all random numbers are drawn on the CPU so that every
back-end sees the same random streams.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

from bh6.backend import make_ops, CHOICE_FILE
from bh6.params import Scenario
from bh6.radio import RadioSource
from bh6.sim import build_world, run_rules

SPECS = [dict(rule="a3", off=3.0, ttt=0.16, name="A3"),
         dict(rule="cho", o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, n_max=4, name="CHO"),
         dict(rule="memcho", o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, n_max=4, w_u=8, w_l=4, w_a=2, v_u=4, v_a=2, name="MemCHO")]
LINES = []


def say(s=""):
    print(s, flush=True)
    LINES.append(s)


def available():
    devs = ["cpu"]
    try:
        import torch
        say("PyTorch %s found; CUDA available: %s" % (torch.__version__, torch.cuda.is_available()))
        devs.append("torch-cpu")
        if torch.cuda.is_available():
            say("GPU: %s, %.1f GB" % (torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory / 2 ** 30))
            devs.append("cuda")
    except Exception as e:
        say("PyTorch not usable (%s): only the NumPy back-end is tested. This is fine; the study runs on the CPU." % type(e).__name__)
    return devs


def one(device, isd=50.0, t_sim=30.0):
    """Radio map, samples and a short simulation with one back-end."""
    ops = make_ops(device)
    sc = Scenario(isd=isd, profile="veh16", t_sim=t_sim, discard=5.0, seed=5, n_ue=60)
    if device != "cpu":                                   # first use of a device includes start-up costs
        build_world(sc.with_(t_sim=1.0, n_ue=4), ops)
    t0 = time.perf_counter()
    w = build_world(sc, ops)
    ops.sync()
    t_map = time.perf_counter() - t0
    src = RadioSource(w.rmap, w.traj, sc)
    t0 = time.perf_counter()
    chunks = [c.rsrp.copy() for c in src.chunks()]
    ops.sync()
    t_samples = time.perf_counter() - t0
    res, eng = run_rules(sc, SPECS, ops=ops, log_events=True, world=w)
    return dict(gain=w.rmap.gain, rsrp=np.concatenate(chunks), logs=[e.log for e in eng], t_map=t_map, t_samples=t_samples,
                t_lookup=src.t_lookup)


def pool_job(a):
    device, seed = a
    sc = Scenario(isd=100.0, profile="veh16", t_sim=40.0, discard=5.0, seed=seed, n_ue=60)
    run_rules(sc, SPECS[:2], ops=make_ops(device))
    return seed


def throughput(device, workers, n_jobs):
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.perf_counter()
    with ProcessPoolExecutor(workers) as ex:
        list(ex.map(pool_job, [(device, 100 + i) for i in range(n_jobs)]))
    return n_jobs / (time.perf_counter() - t0) * 60.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=int(os.environ.get("BH6_WORKERS", "0")) or max(1, (os.cpu_count() or 2) - 4))
    ap.add_argument("--quick", action="store_true", help="skip the multi-process comparison")
    a = ap.parse_args()
    say("Back-end self-test, %s, %d logical CPUs, %d workers" % (time.strftime("%Y-%m-%d %H:%M"), os.cpu_count() or 0, a.workers))
    devs = available()
    say("")
    say("1/2  correctness and single-process time")
    ref = one("cpu")
    say("   cpu (NumPy, reference): radio map %.2f s, radio samples %.2f s (map lookups %.2f s)" % (ref["t_map"], ref["t_samples"], ref["t_lookup"]))
    verified, rows = ["cpu"], {"cpu": dict(t_map=ref["t_map"], t_samples=ref["t_samples"], t_lookup=ref["t_lookup"], verified=True)}
    for d in devs[1:]:
        try:
            r = one(d)
        except Exception as e:
            say("   %s: FAILED to run (%r); not used" % (d, e))
            rows[d] = dict(verified=False, error=repr(e))
            continue
        dg = float(np.abs(r["gain"] - ref["gain"]).max())
        dr = float(np.abs(r["rsrp"] - ref["rsrp"]).max())
        same = r["logs"] == ref["logs"]
        ok = same and dg < 1e-3 and dr < 1e-3
        say("   %s: radio map %.2f s, radio samples %.2f s (lookups %.2f s); largest difference to NumPy: map %.2e dB, samples %.2e dB; "
            "event logs %s -> %s" % (d, r["t_map"], r["t_samples"], r["t_lookup"], dg, dr, "identical" if same else "DIFFERENT",
                                     "verified" if ok else "NOT verified, not used"))
        rows[d] = dict(t_map=r["t_map"], t_samples=r["t_samples"], t_lookup=r["t_lookup"], max_diff_map_db=dg, max_diff_samples_db=dr,
                       logs_identical=same, verified=ok)
        if ok:
            verified.append(d)
    choice = "cpu"
    if not a.quick:
        say("")
        say("3  jobs per minute with %d processes (the real workload)" % a.workers)
        n_jobs = max(2 * a.workers, 8)
        best = 0.0
        for d in verified:
            try:
                jpm = throughput(d, a.workers, n_jobs)
            except Exception as e:
                say("   %s: FAILED with %d processes (%r); not used" % (d, a.workers, e))
                rows[d]["pool_error"] = repr(e)
                continue
            rows[d]["jobs_per_min"] = jpm
            say("   %-10s %.1f jobs per minute" % (d, jpm))
            if d == "cpu" or jpm > best * 1.03:           # another back-end must be at least 3 % faster than the best so far
                best, choice = jpm, d
    say("")
    say("Chosen back-end: %s" % choice)
    if choice == "cpu":
        say("The study will run on the CPU with NumPy. This is the expected outcome on most machines.")
    with open(CHOICE_FILE, "w", encoding="utf-8") as f:
        json.dump(dict(device=choice, verified=verified, workers=a.workers, results=rows, time=time.strftime("%Y-%m-%d %H:%M:%S")), f, indent=1)
    with open(os.path.join(HERE, "selftest_report.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    say("written: backend_choice.json, selftest_report.txt")


if __name__ == "__main__":
    main()
