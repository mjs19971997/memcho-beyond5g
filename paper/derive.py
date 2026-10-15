# -*- coding: utf-8 -*-
"""Numbers of the third paper that are not printed as such in analysis/report.json.

Reads the finished study (results/full_i9/results/full), the calibration against ns-3 and the table of 2026 papers,
and writes data/p3.json.  The manuscript builder (build_p3.js) reads report.json and this file; it never types a
result by hand.

    python derive.py
"""
import csv, gzip, io, json, math, os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
G6 = os.path.dirname(HERE)
# results of the full study: results/full (repository layout) or results/full_i9/results/full (as returned from the run machine)
RES = next(p for p in (os.path.join(G6, "results", "full"), os.path.join(G6, "results", "full_i9", "results", "full")) if os.path.isdir(p))
ANA = os.path.join(RES, "analysis")
SURVEY = os.environ.get("P3_SURVEY", os.path.join(HERE, "data", "survey_2026.csv"))      # 15 handover studies of 2026, read in full
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

import numpy as np
from scipy import stats

R = json.load(open(os.path.join(ANA, "report.json"), encoding="utf-8"))


def tci(a):
    a = np.asarray(a, float)
    m = a.mean()
    h = stats.t.ppf(0.975, len(a) - 1) * a.std(ddof=1) / math.sqrt(len(a)) if len(a) > 1 else float("nan")
    return dict(mean=m, lo=m - h, hi=m + h, n=len(a))


# ------------------------------------------------------------------ runs.csv
rows = list(csv.DictReader(open(os.path.join(ANA, "runs.csv"), encoding="utf-8")))
out = dict(n_rule_runs=len(rows), rule_runs_by_stage={})
for r in rows:
    out["rule_runs_by_stage"][r["stage"]] = out["rule_runs_by_stage"].get(r["stage"], 0) + 1

KEYS = ["uho_pm", "fail_pm", "prep_mean", "delivered", "reports_pm", "int_s_pm", "cfg_lost_pm", "prep_req_pm", "prep_wasted_pm",
        "att_pm", "pp_pm", "uho_and_pm", "rate_mbps", "rel_pm", "late_pm", "sinr_db",
        "f_late_cmd_pm", "f_late_prep_pm", "f_late_rlf_pm", "f_cov_rlf_pm", "f_exec_fail_pm", "f_early_rlf_pm"]
by = defaultdict(lambda: defaultdict(list))
for r in rows:
    if r["stage"] in ("S1", "X3", "O3"):
        for k in KEYS:
            by[(r["stage"], r["rule"])][k].append(float(r[k]))
out["ci"] = {f"{s}|{rule}": {k: tci(v) for k, v in d.items()} for (s, rule), d in by.items()}

# reference of the sensitivity stage: S1 runs of the three conditions and the twelve seeds that S3 uses
cells = {(100, "veh16"), (100, "ped"), (50, "veh16")}
base = defaultdict(dict)
for r in rows:
    if r["stage"] == "S1" and (int(r["isd"]), r["profile"]) in cells and int(r["seed"]) <= 12 and r["rule"] in ("cho@std", "memcho@std", "a3@std"):
        base[(r["isd"], r["profile"], r["seed"])][r["rule"]] = r
pairs = list(base.values())
d_u = [float(p["memcho@std"]["uho_pm"]) - float(p["cho@std"]["uho_pm"]) for p in pairs]
d_f = [float(p["memcho@std"]["fail_pm"]) - float(p["cho@std"]["fail_pm"]) for p in pairs]
mu_c = np.mean([float(p["cho@std"]["uho_pm"]) for p in pairs]); mu_m = np.mean([float(p["memcho@std"]["uho_pm"]) for p in pairs])
ci = tci(d_u)
out["s3_base"] = dict(n=len(pairs), uho_cho=mu_c, uho_mem=mu_m, rel_pct=100 * (mu_m - mu_c) / mu_c,
                      rel_lo=100 * ci["lo"] / mu_c, rel_hi=100 * ci["hi"] / mu_c,
                      p=float(stats.wilcoxon(d_u).pvalue), fail_cho=np.mean([float(p["cho@std"]["fail_pm"]) for p in pairs]),
                      fail_mem=np.mean([float(p["memcho@std"]["fail_pm"]) for p in pairs]), fail_diff=tci(d_f))

# ------------------------------------------------------------------ memory over time (event logs, S1 seeds 1-10)
WIN = 6
edges = np.linspace(60.0, 660.0, WIN + 1)
cnt = defaultdict(lambda: np.zeros(WIN)); thirds = defaultdict(lambda: np.zeros(3)); nrun = 0
ev = os.path.join(RES, "events", "S1")
for f in sorted(os.listdir(ev)):
    nrun += 1
    with gzip.open(os.path.join(ev, f), "rt", encoding="utf-8") as h:
        for r in csv.DictReader(h):
            if r["outcome"] != "unnecessary":
                continue
            t = float(r["t_attempt"])
            if 60.0 <= t < 660.0:
                cnt[r["rule"]][min(int((t - 60.0) / (600.0 / WIN)), WIN - 1)] += 1
                thirds[r["rule"]][min(int((t - 60.0) / 200.0), 2)] += 1
uemin = 60 * (600.0 / WIN) / 60.0          # 60 UEs x window length in minutes
out["windows"] = dict(n_runs=nrun, edges=list(edges), rate={k: list(v / (nrun * uemin)) for k, v in cnt.items()},
                      thirds={k: list(v / (nrun * 60 * 200 / 60.0)) for k, v in thirds.items()})
for k, v in R["windows"].items():           # the thirds must equal those of the analysis report
    got = out["windows"]["thirds"][k]
    if max(abs(a - b) for a, b in zip(got, v)) > 2e-3:
        sys.exit("time windows do not reproduce report.json for %s: %s vs %s" % (k, got, v))

# ------------------------------------------------------------------ calibration against ns-3
C = json.load(open(os.path.join(G6, "calibration.json"), encoding="utf-8"))
out["calib"] = dict(summary=C["summary"], partA=[dict(hyst=a["hyst"], ttt=a["ttt"], ns3=a["ns3"], sim=a["sim"]) for a in C["partA"]])

# ------------------------------------------------------------------ survey of 2026 papers
P = list(csv.DictReader(io.open(SURVEY, encoding="utf-8-sig")))
def has(r, k, *w):
    return any(x in r[k].lower() for x in w)
sv = dict(n=len(P))
sv["own_or_unnamed"] = sum(r["tool_class"] == "own / not stated" for r in P)
sv["traces"] = sum(r["tool_class"] == "real traces / dataset" for r in P)
sv["standard_sim"] = sum(r["tool_class"] in ("ns-3", "OMNeT++", "MATLAB", "Sionna") for r in P)
sv["fr3"] = sum(r["band_class"] == "FR3 (7-24 GHz)" for r in P)
sv["band_not_stated"] = sum(r["band_class"] == "not stated" for r in P)
sv["spread"] = sum(has(r, "statistics", "ci", "std") and not has(r, "statistics", "no ci") for r in P)
sv["test"] = sum(has(r, "statistics", "wilcoxon", "t-test", "paired test", "significance") for r in P)
sv["code"] = sum(r["code"].lower().startswith("yes") for r in P)
sv["ch3gpp"] = sum(has(r, "channel_model", "38.901", "38.811") for r in P)
sv["cho_baseline"] = sum(has(r, "baselines", "cho") for r in P)
sv["fixed_a3"] = sum(has(r, "baselines", "a3", "rss") for r in P)
sv["fail_metric"] = sum(has(r, "metrics", "failure", "rlf", "reliability", "outage") for r in P)
sv["interruption"] = sum(has(r, "metrics", "interruption", "latency", "delay") for r in P)
sv["prep_metric"] = sum(has(r, "metrics", "preparation", "signalling", "switching cost") for r in P)
sv["rows"] = [dict(title=r["title"], tool=r["tool_class"], band=r["band_class"], stats=r["statistics"], code=r["code"], url=r["doi_or_url"]) for r in P]
out["survey"] = sv

# ------------------------------------------------------------------ simulated network, for the scenario figure and the text
sys.path.insert(0, G6)
from bh6.layout import grid_layout
out["sites"] = {str(d): len(grid_layout(float(d)).sites) for d in (50, 100, 150)}
from bh6.params import Scenario
from bh6 import study, policies, services, mobility
import inspect
out["scenario"] = Scenario().to_dict()
out["design"] = {k: (list(v) if isinstance(v, tuple) else v) for k, v in study.DESIGNS["full"].items()}
out["grids"] = {m: dict(label=v["label"], grid={k: list(g) for k, g in v["grid"].items()}, fixed=v.get("fixed", {})) for m, v in study.METHODS.items()}
out["sens"] = {k: v for k, v in study.SENS.items()}
mc = inspect.signature(policies.MemCho.__init__).parameters
out["memcho_const"] = dict(O_LO=policies.MemCho.O_LO, O_HI=policies.MemCho.O_HI, REP_CAP=policies.MemCho.REP_CAP,
                           kappa=mc["kappa"].default, kappa0=mc["kappa0"].default, res=mc["res"].default, tau=mc["tau"].default,
                           t_p=mc["t_p"].default, half_angle=inspect.signature(policies.path_overlap).parameters["half_angle"].default,
                           r_min=inspect.signature(policies.path_overlap).parameters["r_min"].default, stick=policies.Cho.stick,
                           strict=study.STRICT, uho_tol=study.UHO_TOL, ref=study.REF_A3)
out["services"] = [dict(key=s.key, fiveqi=s.fiveqi, t_min=s.t_min, theta_q=s.theta_q, share=s.share, rate=s.rate_mbps) for s in services.SERVICES]
out["profiles"] = {k: v for k, v in mobility.PROFILES.items() if k in ("ped", "veh8", "veh16", "veh30", "mix")}

json.dump(out, open(os.path.join(OUT, "p3.json"), "w", encoding="utf-8"), indent=1, default=float)
print("p3.json written:", out["n_rule_runs"], "rule-runs;", "survey", {k: v for k, v in sv.items() if k != "rows"}, "| sites", out["sites"],
      "| S3 base", round(out["s3_base"]["rel_pct"], 1), "| windows", {k: [round(x, 3) for x in v] for k, v in out["windows"]["rate"].items()})
