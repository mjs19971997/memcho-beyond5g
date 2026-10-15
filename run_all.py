# -*- coding: utf-8 -*-
"""Run the whole study, stage by stage.  Safe to stop and start again at any time.

    python run_all.py                 the full study (resumes where it stopped)
    python run_all.py --smoke         a short end-to-end test (a few minutes)
    python run_all.py --status        progress and remaining time, without running anything
    python run_all.py --only S1,S2    only some stages
    python run_all.py --workers 24 --device cpu

Options can also come from the environment: BH6_WORKERS, BH6_DEVICE.
Results go to results/<design>/ (one JSON file per job).  A finished job is
never run again; a failed job is listed at the end and tried again on the next
start.  After the last stage the analysis runs and everything is packed into
g6study_outputs.zip (see collect_outputs.py).
"""
import argparse
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "1")          # one thread per worker process; the parallelism is over jobs

from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures.process import BrokenProcessPool

from bh6 import study
from bh6.backend import resolve_device

LOG = None
SMOKE_SCALE = 2.0     # cost per simulated second of a full-design rule-run relative to a smoke rule-run
                      # (60 instead of 20 users, more sites, more learning rules); measured on the development server


def log(msg):
    line = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(line, flush=True)
    if LOG:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def out_dir(design):
    return os.path.join(HERE, "results", design)


def fail_path(outdir, job):
    return os.path.join(outdir, "failed", job["id"] + ".txt")


def scan(design, outdir, stages):
    """Per stage: (jobs or None, done ids, failed ids)."""
    info = {}
    for st in stages:
        jobs = study.stage_jobs(st, design, outdir)
        if jobs is None:
            info[st] = (None, [], [])
            continue
        done = [j for j in jobs if os.path.exists(study.job_path(outdir, j))]
        failed = [j for j in jobs if os.path.exists(fail_path(outdir, j)) and not os.path.exists(study.job_path(outdir, j))]
        info[st] = (jobs, done, failed)
    return info


def measured_rate(outdir):
    """Mean seconds of one rule-run and of the per-job overhead, from the finished jobs."""
    import json
    n = tot = over = nj = 0
    root = os.path.join(outdir, "jobs")
    for dp, _, files in os.walk(root):
        for fn in files[:40]:
            if fn.endswith(".json"):
                try:
                    with open(os.path.join(dp, fn), "r", encoding="utf-8") as f:
                        r = json.load(f)
                    tot += r["timing"]["engine_s"]; n += len(r["results"])
                    over += r["wall_s"] - r["timing"]["engine_s"]; nj += 1
                except (OSError, ValueError, KeyError):
                    pass
    return (tot / n if n else None), (over / nj if nj else None)


def status(design, outdir, stages, workers):
    info = scan(design, outdir, stages)
    per_run, per_job = measured_rate(outdir)
    print("design: %s    results: %s" % (design, outdir))
    print("%-5s %8s %8s %8s %10s %12s" % ("stage", "jobs", "done", "failed", "rule-runs", "hours left"))
    left_total = 0.0
    for st in stages:
        jobs, done, failed = info[st]
        nj, nr = study.planned_count(st, design)
        if jobs is not None:
            nj = len(jobs); nr = sum(len(j["specs"]) for j in jobs)
            ids = {j["id"] for j in done}
            rem_jobs = [j for j in jobs if j["id"] not in ids]
            rem_runs = sum(len(j["specs"]) for j in rem_jobs)
        else:
            rem_jobs, rem_runs = None, nr
        if per_run is not None:
            h = (rem_runs * per_run + (len(rem_jobs) if rem_jobs is not None else nj) * per_job) / 3600.0 / max(workers, 1)
            left_total += h
            hs = "%.2f" % h
        else:
            hs = "?"
        print("%-5s %8d %8s %8d %10d %12s%s" % (st, nj, len(done) if jobs is not None else "-", len(failed), nr, hs,
                                               "" if jobs is not None else "   (waits for an earlier stage)"))
    if per_run is not None:
        print("measured: %.1f s per rule-run, %.1f s overhead per job; about %.1f h left with %d workers "
              "(assuming all workers are equally fast)" % (per_run, per_job, left_total, workers))
    elif design != "smoke":
        s_run, s_job = measured_rate(out_dir("smoke"))
        if s_run is not None:
            k = study.DESIGNS[design]["t_sim"] / study.DESIGNS["smoke"]["t_sim"] * SMOKE_SCALE
            runs = sum(study.planned_count(st, design)[1] for st in stages)
            njobs = sum(study.planned_count(st, design)[0] for st in stages)
            h = (runs * s_run * k + njobs * s_job * 0.3 * k) / 3600.0 / max(workers, 1)
            print("no job of this design has finished yet. Projection from the smoke test on this machine "
                  "(%.1f s per smoke rule-run): about %.1f h with %d workers. Rough: the smoke test is small." % (s_run, h, workers))
        else:
            print("no timing yet: run  python run_all.py --smoke  first, then --status shows a projection.")
    if os.path.exists(os.path.join(outdir, "RUN_ALL_DONE")):
        print("RUN_ALL_DONE is present: the last complete pass finished.")


def run_stage(st, design, outdir, workers, device):
    jobs = study.stage_jobs(st, design, outdir)
    if jobs is None:
        log("stage %s: skipped, an earlier stage it needs is not complete" % st)
        return 0, 0
    todo = [j for j in jobs if not os.path.exists(study.job_path(outdir, j))]
    log("stage %s: %d jobs, %d already done, %d to run (%d rule-runs)" %
        (st, len(jobs), len(jobs) - len(todo), len(todo), sum(len(j["specs"]) for j in todo)))
    os.makedirs(os.path.join(outdir, "failed"), exist_ok=True)
    t0 = time.time()
    n_ok = n_bad = 0
    # the longest jobs first, so that the tail of a stage is short
    todo.sort(key=lambda j: -len(j["specs"]))
    for attempt in (1, 2):
        if not todo:
            break
        rest = {j["id"]: j for j in todo}
        try:
            with ProcessPoolExecutor(max_workers=min(workers, len(todo))) as ex:
                futs = {ex.submit(study.run_job, j, design, outdir, device): j for j in todo}
                for fu in as_completed(futs):
                    j = futs[fu]
                    try:
                        jid, err, sec = fu.result()
                    except BrokenProcessPool:
                        raise
                    except Exception as e:                       # the worker itself broke for this job
                        jid, err, sec = j["id"], repr(e), 0.0
                    rest.pop(jid, None)
                    if err is None:
                        n_ok += 1
                        if os.path.exists(fail_path(outdir, j)):
                            os.remove(fail_path(outdir, j))
                    else:
                        n_bad += 1
                        with open(fail_path(outdir, j), "w", encoding="utf-8") as f:
                            f.write(err)
                        log("  FAILED %s: %s" % (jid, err.strip().splitlines()[-1][:200]))
                    k = n_ok + n_bad
                    if k % max(1, len(futs) // 20) == 0 or k == len(futs):
                        el = time.time() - t0
                        log("  %s: %d/%d jobs, %.1f min elapsed, about %.1f min left" %
                            (st, k, len(futs), el / 60.0, el / max(k, 1) * (len(futs) - k) / 60.0))
            todo = []
        except BrokenProcessPool:
            todo = list(rest.values())
            log("  a worker process died; %d jobs of stage %s are started again (attempt %d)" % (len(todo), st, attempt))
    for j in todo:                                                 # still unfinished after the second attempt
        n_bad += 1
        with open(fail_path(outdir, j), "w", encoding="utf-8") as f:
            f.write("worker process died twice\n")
    log("stage %s finished: %d ok, %d failed, %.1f min" % (st, n_ok, n_bad, (time.time() - t0) / 60.0))
    return n_ok, n_bad


def main():
    global LOG
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--design", default="full", choices=sorted(study.DESIGNS))
    ap.add_argument("--smoke", action="store_true", help="short end-to-end test (same as --design smoke)")
    ap.add_argument("--pilot", action="store_true", help="the small pilot (same as --design pilot)")
    ap.add_argument("--status", action="store_true", help="show progress and exit")
    ap.add_argument("--only", default="", help="comma-separated stages, e.g. T1,T2,S1")
    ap.add_argument("--workers", type=int, default=int(os.environ.get("BH6_WORKERS", "0")))
    ap.add_argument("--device", default=os.environ.get("BH6_DEVICE", "auto"), help="auto, cpu, cuda or torch-cpu")
    ap.add_argument("--no-analyze", action="store_true")
    a = ap.parse_args()
    design = "smoke" if a.smoke else "pilot" if a.pilot else a.design
    workers = a.workers or max(1, (os.cpu_count() or 2) - 4)
    stages = [s for s in study.DESIGNS[design].get("stages", study.STAGES) if not a.only or s in a.only.split(",")]
    outdir = out_dir(design)
    if a.status:
        status(design, outdir, stages, workers)
        return 0
    os.makedirs(outdir, exist_ok=True)
    LOG = os.path.join(outdir, "run_all.log")
    device = resolve_device(a.device)
    done_flag = os.path.join(outdir, "RUN_ALL_DONE")
    if os.path.exists(done_flag):
        os.remove(done_flag)
    log("run_all: design %s, %d workers, device %s (asked: %s), stages %s" % (design, workers, device, a.device, ",".join(stages)))
    t0 = time.time()
    tot_ok = tot_bad = 0
    for st in stages:
        ok, bad = run_stage(st, design, outdir, workers, device)
        tot_ok += ok; tot_bad += bad
    failed = sorted(f[:-4] for f in os.listdir(os.path.join(outdir, "failed"))) if os.path.isdir(os.path.join(outdir, "failed")) else []
    log("all stages passed once: %d jobs run now, %.2f h" % (tot_ok, (time.time() - t0) / 3600.0))
    log("failed jobs: %d" % len(failed))
    for f in failed:
        log("  failed: %s  (see results/%s/failed/%s.txt; start run_all.py again to retry)" % (f, design, f))
    if not a.no_analyze:
        try:
            import analyze
            analyze.run(design)
            log("analysis written to results/%s/analysis" % design)
        except Exception as e:
            log("analysis failed: %r (the result files are complete; run analyze.py again)" % (e,))
        try:
            import collect_outputs
            z = collect_outputs.collect(design)
            log("outputs packed: %s" % z)
        except Exception as e:
            log("packing failed: %r (run collect_outputs.py)" % (e,))
    with open(done_flag, "w", encoding="utf-8") as f:
        f.write("%s failed=%d\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), len(failed)))
    log("RUN_ALL_DONE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
