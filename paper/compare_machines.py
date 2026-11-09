# -*- coding: utf-8 -*-
"""Cross-machine determinism from existing results only (no new simulation).

Part of the run with widened baseline grids was first started on the development server (results/full_ext_server_partial:
all of T1 and 45 of the 162 jobs of T2) and then run in full on a second machine (results/full_ext).  Jobs that both
machines simulated themselves are compared rule by rule: every count field must be equal, and the largest absolute and
relative difference of the real-valued fields is reported.  Rows that a job took over from the first run ("reused") and
job files that were copied from one machine to the other (byte-identical) are not counted as independent evidence.

    python compare_machines.py <server folder> <second-machine folder>      -> data/determinism_check.json
"""
import filecmp, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A, B = sys.argv[1], sys.argv[2]
out = dict(jobs=[], note=__doc__.strip().splitlines()[0])
for stage in sorted(os.listdir(os.path.join(A, "jobs"))):
    for fn in sorted(os.listdir(os.path.join(A, "jobs", stage))):
        pa, pb = os.path.join(A, "jobs", stage, fn), os.path.join(B, "jobs", stage, fn)
        if not os.path.exists(pb) or filecmp.cmp(pa, pb, shallow=False):
            continue                                            # missing on the second machine, or a copied file
        a, b = json.load(io.open(pa, encoding="utf-8")), json.load(io.open(pb, encoding="utf-8"))
        reused = set(a.get("reused", [])) | set(b.get("reused", []))
        ra = {r["rule"]: r for r in a["results"] if r["rule"] not in reused}
        rb = {r["rule"]: r for r in b["results"] if r["rule"] not in reused}
        common = sorted(set(ra) & set(rb))
        if not common:
            continue
        nf = ncount = cdiff = 0; maxabs = maxrel = 0.0
        for k in common:
            for f, x in ra[k].items():
                y = rb[k].get(f)
                if f in ("wall_s",) or isinstance(x, bool) or not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    continue
                nf += 1
                if f.startswith(("c_", "n_")):
                    ncount += 1; cdiff += x != y
                d = abs(x - y); maxabs = max(maxabs, d)
                if x:
                    maxrel = max(maxrel, d / abs(x))
        out["jobs"].append(dict(id=fn[:-5], rules=len(common), numeric_fields=nf, count_fields=ncount, count_fields_differing=cdiff,
                                max_abs_diff=maxabs, max_rel_diff=maxrel))
J = out["jobs"]
out["summary"] = dict(jobs=len(J), rules=sum(j["rules"] for j in J), numeric_fields=sum(j["numeric_fields"] for j in J),
                      count_fields=sum(j["count_fields"] for j in J), count_fields_differing=sum(j["count_fields_differing"] for j in J),
                      max_abs_diff=max(j["max_abs_diff"] for j in J), max_rel_diff=max(j["max_rel_diff"] for j in J))
json.dump(out, io.open(os.path.join(HERE, "data", "determinism_check.json"), "w", encoding="utf-8"), indent=1)
print(out["summary"])
