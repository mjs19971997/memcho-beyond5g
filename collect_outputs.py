# -*- coding: utf-8 -*-
"""Pack everything that has to be sent back into one zip file.

    python collect_outputs.py                 full study  -> g6study_outputs.zip
    python collect_outputs.py --design smoke  smoke test  -> g6study_outputs_smoke.zip

The zip is written next to this script, always at the same path.  It contains
the result files of all jobs, the frozen settings, the analysis (report,
tables, figures), the event logs, the run log, the list of failed jobs, the
plan, the check reports and the back-end self-test.  It can be created at any
time, also for an unfinished run.
"""
import argparse
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
EXTRA = ("PLAN.md", "LITERATURE.md", "checks_report.txt", "calibration_report.txt", "calibration.json",
         "backend_choice.json", "selftest_report.txt", "requirements.txt")


def collect(design="full"):
    """Create the zip for ``design`` and return its path."""
    outdir = os.path.join(HERE, "results", design)
    name = "g6study_outputs.zip" if design == "full" else "g6study_outputs_%s.zip" % design
    path = os.path.join(HERE, name)
    tmp = path + ".tmp"
    n = 0
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for dp, _, files in os.walk(outdir):
            for fn in sorted(files):
                if fn.endswith(".tmp"):
                    continue
                full = os.path.join(dp, fn)
                z.write(full, os.path.join("results", design, os.path.relpath(full, outdir)))
                n += 1
        for fn in EXTRA:
            if os.path.exists(os.path.join(HERE, fn)):
                z.write(os.path.join(HERE, fn), fn)
                n += 1
    os.replace(tmp, path)
    print("%d files packed into %s (%.1f MB)" % (n, path, os.path.getsize(path) / 1e6))
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="full")
    collect(ap.parse_args().design)
