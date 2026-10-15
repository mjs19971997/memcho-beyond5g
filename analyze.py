# -*- coding: utf-8 -*-
"""Tables, tests and figures from the result files.

    python analyze.py                  analysis of the full study
    python analyze.py --design smoke   analysis of another design

Reads results/<design>/jobs/**.json and writes to results/<design>/analysis/:
report.txt (all tables and tests), report.json (the same numbers), CSV files
(one row per run and rule) and PNG figures.  It works on whatever is finished:
a stage that has no results is reported as "not run".

Statistics as fixed in PLAN.md: methods paired by seed, exact Wilcoxon
signed-rank test, mean paired difference with a 95 % t interval, Holm
correction for the three parts of the main hypothesis.
"""
import argparse
import csv
import glob
import gzip
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

from bh6 import study
from bh6.stats import paired, holm, rnd

MAIN = list(study.MAIN)
LABEL = {"a3": "A3", "pum": "Per-user margin", "cho": "CHO", "memcho": "MemCHO", "mc_exec": "MemCHO, execution only",
         "mc_prep": "MemCHO, preparation only", "mc_mem": "MemCHO, memory only", "mc_mot": "MemCHO, motion only",
         "mc_pair": "MemCHO, cell-pair memory"}
ENDPOINTS = [("uho_pm", "unnecessary handovers / UE-min"), ("fail_pm", "failures / UE-min"),
             ("prep_mean", "mean prepared cells"), ("int_s_pm", "interruption s / UE-min"),
             ("delivered", "delivered share of demand"), ("rate_mbps", "delivered rate Mbit/s per user"),
             ("att_pm", "handover attempts / UE-min")]
CAUSES = [("f_late_cmd_pm", "command lost"), ("f_late_prep_pm", "link failure during preparation"),
          ("f_late_rlf_pm", "link failure, no handover"), ("f_exec_fail_pm", "execution failed"),
          ("f_early_rlf_pm", "link failure in the target"), ("f_cov_rlf_pm", "coverage")]
# categorical colours in fixed order (checked for colour-vision separation); markers repeat the identity
COLORS = {"a3": "#2a78d6", "pum": "#eb6834", "cho": "#1baf7a", "memcho": "#eda100"}
MARKS = {"a3": "o", "pum": "s", "cho": "^", "memcho": "D"}
CAUSE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


# ----------------------------------------------------------------------------
def load(outdir):
    """All finished jobs: list of (job meta, {rule name: metrics}, timing)."""
    jobs = []
    for path in sorted(glob.glob(os.path.join(outdir, "jobs", "*", "*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                r = json.load(f)
        except (OSError, ValueError):
            continue
        jobs.append((r["job"], dict(zip(r["names"], r["results"])), r.get("timing", {}), r.get("wall_s", 0.0)))
    return jobs


def pairs(runs, new, ref, key):
    """Paired arrays of metric ``key`` over the runs that contain both rules."""
    a = [r[new][key] for r in runs if new in r and ref in r]
    b = [r[ref][key] for r in runs if new in r and ref in r]
    return np.array(a), np.array(b)


def fmt_cmp(c, nd=3):
    return "%s -> %s  diff %s [%s, %s]  %s %%  p = %.2g  (n = %d)" % (
        rnd(c["mean_ref"], nd), rnd(c["mean_new"], nd), rnd(c["diff"], nd), rnd(c["ci_lo"], nd), rnd(c["ci_hi"], nd),
        rnd(c["rel_pct"], 1), c["p"], c["n"])


class Report:
    def __init__(self):
        self.lines, self.data = [], {}

    def w(self, s=""):
        self.lines.append(s)

    def h(self, s):
        self.lines += ["", s, "=" * len(s)]


def means_table(R, runs, names, keys, title):
    R.w(title)
    R.w("%-28s" % "rule" + "".join("%12s" % k.replace("_pm", "").replace("f_", "").replace("rate_mbps", "rate_Mbps")[:11] for k in keys) + "%6s" % "n")
    out = {}
    for n in names:
        sel = [r[n] for r in runs if n in r]
        if not sel:
            continue
        m = {k: float(np.mean([x[k] for x in sel])) for k in keys}
        out[n] = m
        R.w("%-28s" % n + "".join("%12s" % rnd(m[k], 3) for k in keys) + "%6d" % len(sel))
    return out


def comparisons(R, runs, pairs_list, keys, tag):
    out = {}
    for new, ref in pairs_list:
        if not any(new in r and ref in r for r in runs):
            continue
        R.w("%s against %s" % (new, ref))
        for k, lab in keys:
            a, b = pairs(runs, new, ref, k)
            c = paired(a, b)
            out["%s|%s|%s" % (new, ref, k)] = c
            R.w("   %-32s %s" % (lab, fmt_cmp(c)))
    R.data[tag] = out
    return out


# ----------------------------------------------------------------------------
def section_tuning(R, outdir, env):
    path = study.tuned_path(outdir, env)
    if not os.path.exists(path):
        R.w("tuning (%s): not complete" % env)
        return None
    with open(path, "r", encoding="utf-8") as f:
        tn = json.load(f)
    R.w("Selection rule: " + tn["_selection"])
    rows = []
    for isd, node in tn["isd"].items():
        R.w("")
        R.w("site distance %s m: failure budget %s (standard, = reference A3 3 dB / 160 ms on the validation traces), %s (strict)" %
            (isd, rnd(node["budget"]["std"], 4), rnd(node["budget"]["strict"], 4)))
        for m, mn in node["methods"].items():
            for b in ("std", "strict"):
                s = mn[b]
                par = ", ".join("%s=%g" % (k, v) for k, v in sorted(s["spec"].items()) if k not in ("rule", "name") and not isinstance(v, bool))
                R.w("   %-8s %-6s %-14s UHO %s  fail %s  prepared %s  %s  [%s]" %
                    (m, b, s["name"], rnd(s["uho"], 3), rnd(s["fail"], 4), rnd(s["prep"], 3),
                     "meets budget (%d of %d do)" % (s["n_meeting"], len(mn["settings"])) if s["met_budget"] else "NO setting meets the budget", par))
            for s in mn["settings"]:
                rows.append([env, isd, m, s["name"], s["uho"], s["fail"], s["prep"], s["ho"], json.dumps(s["spec"], sort_keys=True)])
    with open(os.path.join(outdir, "analysis", "tuning_%s.csv" % env), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["env", "isd", "method", "setting", "val_uho_pm", "val_fail_pm", "val_prep_mean", "val_att_pm", "parameters"])
        wr.writerows(rows)
    R.data["tuning_" + env] = tn["isd"]
    return tn


def section_test(R, jobs, stage, tag, tn):
    sel = [(j, res) for j, res, _, _ in jobs if j["stage"] == stage]
    if not sel:
        R.w("stage %s: not run" % stage)
        return None
    runs = [res for _, res in sel]
    methods = sorted({n.split("@")[0] for r in runs for n in r if n.endswith("@std")}, key=lambda m: (list(LABEL).index(m) if m in LABEL else 99))
    R.w("%d runs (condition x seed), %s UE-minutes each" % (len(runs), rnd(runs[0][next(iter(runs[0]))]["ue_min"], 0)))
    keys = [k for k, _ in ENDPOINTS] + ["late_pm", "uho_and_pm", "pp_pm"]
    R.w("")
    m_std = means_table(R, runs, ["a3@ref"] + [m + "@std" for m in methods], keys, "Means, standard budget")
    R.w("")
    m_str = means_table(R, runs, [m + "@strict" for m in methods], keys, "Means, strict budget")
    R.data[tag + "_means_std"], R.data[tag + "_means_strict"] = m_std, m_str
    R.w("")
    means_table(R, runs, [m + "@std" for m in methods], [k for k, _ in CAUSES] + ["fail_pm", "late_rlf_prepared_pm", "rec_pm"],
                "Failures by cause per UE-minute, standard budget (late_rlf_prepared: of the 'no handover' failures, those with a prepared cell; rec: recoveries into a prepared cell)")
    R.w("")
    means_table(R, runs, [m + "@std" for m in methods if m not in ("a3", "pum")],
                ["prep_mean", "prep_req_pm", "prep_wasted_pm", "cfg_lost_pm", "reports_pm", "rel_pm"], "Preparation overhead, standard budget")
    # premises
    R.w("")
    R.w("Premises")
    for m in ("a3", "pum"):
        n = m + "@std"
        tot = sum(r[n]["c_fail"] for r in runs if n in r)
        late = sum(r[n]["c_f_late_cmd"] + r[n]["c_f_late_prep"] + r[n]["c_f_late_rlf"] for r in runs if n in r)
        R.w("   P1  %s: %d failures, %d late (%s %%)" % (n, tot, late, rnd(100.0 * late / tot, 1) if tot else "n/a"))
        R.data["%s_P1_%s" % (tag, m)] = dict(failures=tot, late=late)
    ep = ENDPOINTS[:6] + [("late_pm", "late failures / UE-min"), ("uho_and_pm", "UHO, short and low gain"), ("pp_pm", "ping-pongs / UE-min")]
    R.w("")
    R.w("Paired comparisons, standard budget (reference -> new, mean difference with 95 % interval, relative change, exact Wilcoxon p)")
    cl = [("memcho@std", "cho@std"), ("cho@std", "a3@std"), ("pum@std", "a3@std"), ("memcho@std", "a3@std"), ("memcho@std", "pum@std")]
    cl += [("memcho@std", a + "@std") for a in methods if a.startswith("mc_")]
    cmp_std = comparisons(R, runs, cl, ep, tag + "_cmp_std")
    R.w("")
    R.w("Paired comparisons, strict budget")
    comparisons(R, runs, [(a.replace("@std", "@strict"), b.replace("@std", "@strict")) for a, b in cl], ep[:5], tag + "_cmp_strict")
    # main hypothesis
    k = "memcho@std|cho@std|"
    if k + "uho_pm" in cmp_std and tn is not None:
        budget = float(np.mean([n["budget"]["std"] for n in tn["isd"].values()]))
        a, b, c = cmp_std[k + "uho_pm"], cmp_std[k + "fail_pm"], cmp_std[k + "prep_mean"]
        adj = holm([a["p"], b["p"], c["p"]])
        margin = 0.2 * budget
        R.w("")
        R.w({"S1": "Main hypothesis H1 (MemCHO against CHO, standard budget)",
             "O3": "Boundary B1 (MemCHO against CHO in the open area)"}.get(stage, "MemCHO against CHO, same three criteria (not part of H1)"))
        R.w("   (a) unnecessary handovers lower:   diff %s, Holm p = %.2g  -> %s" %
            (rnd(a["diff"], 3), adj[0], "holds" if a["diff"] < 0 and adj[0] < 0.05 else "does not hold"))
        R.w("   (b) failures not higher: upper end %s against margin %s (0.2 x mean budget %s) -> %s; Holm p of the difference = %.2g" %
            (rnd(b["ci_hi"], 4), rnd(margin, 4), rnd(budget, 4), "holds" if b["ci_hi"] < margin else "does not hold", adj[1]))
        R.w("   (c) prepared set smaller:          diff %s, Holm p = %.2g  -> %s" %
            (rnd(c["diff"], 3), adj[2], "holds" if c["diff"] < 0 and adj[2] < 0.05 else "does not hold"))
        R.data[tag + "_H1"] = dict(uho=a, fail=b, prep=c, holm=adj, margin=margin)
    # per condition
    R.w("")
    R.w("Per condition, standard budget: means of A3 / per-user margin / CHO / MemCHO, and MemCHO - CHO")
    cells = sorted({(j["isd"], j["profile"]) for j, _ in sel})
    percell = {}
    for isd, prof in cells:
        rr = [res for j, res in sel if j["isd"] == isd and j["profile"] == prof]
        R.w("   site distance %d m, %s (%d seeds)" % (isd, prof, len(rr)))
        for key, lab in ENDPOINTS[:3]:
            vals = [rnd(np.mean([r[m + "@std"][key] for r in rr if m + "@std" in r]), 3) for m in MAIN]
            a, b = pairs(rr, "memcho@std", "cho@std", key)
            c = paired(a, b)
            percell["%d|%s|%s" % (isd, prof, key)] = c
            R.w("      %-30s %s   diff %s [%s, %s], p = %.2g" % (lab, " / ".join(vals), rnd(c["diff"], 3), rnd(c["ci_lo"], 3), rnd(c["ci_hi"], 3), c["p"]))
    R.data[tag + "_percell"] = percell
    return dict(runs=runs, sel=sel, methods=methods, means=m_std, percell=percell, cells=cells)


def section_frontier(R, jobs, tn):
    sel = [(j, res) for j, res, _, _ in jobs if j["stage"] == "S2"]
    if not sel or tn is None:
        R.w("stage S2: not run")
        return None
    front = {}
    levels = (0.25, 0.5, 1.0, 2.0)
    R.w("Per site distance: every tuned setting pooled over the S2 runs; then, for a failure level, the setting of each")
    R.w("method with the lowest unnecessary-handover rate among those not above the level (chosen on these same runs: descriptive).")
    pooled = defaultdict(list)
    for isd in sorted({j["isd"] for j, _ in sel}):
        budget = tn["isd"][str(isd)]["budget"]["std"]
        per = {}
        for m in MAIN:
            rr = {(j["profile"], j["seed"]): res for j, res in sel if j["isd"] == isd and j["method"] == m}
            if not rr:
                continue
            names = sorted(next(iter(rr.values())))
            pts = [(n, float(np.mean([r[n]["uho_pm"] for r in rr.values()])), float(np.mean([r[n]["fail_pm"] for r in rr.values()])),
                    float(np.mean([r[n]["prep_mean"] for r in rr.values()]))) for n in names]
            per[m] = (rr, pts)
            front["%d|%s" % (isd, m)] = pts
        R.w("")
        R.w("site distance %d m, standard budget %s" % (isd, rnd(budget, 4)))
        for lv in levels:
            lim = lv * budget
            best = {}
            for m, (rr, pts) in per.items():
                ok = [p for p in pts if p[2] <= lim + 1e-12]
                if ok:
                    best[m] = min(ok, key=lambda p: (p[1], p[2]))
            txt = "; ".join("%s %s UHO %s fail %s prep %s" % (m, b[0].split("/")[-1], rnd(b[1], 3), rnd(b[2], 4), rnd(b[3], 2)) for m, b in best.items())
            R.w("   failures <= %s x budget (%s): %s" % (rnd(lv, 2), rnd(lim, 4), txt if txt else "no setting"))
            for new, ref in (("memcho", "cho"), ("cho", "a3"), ("pum", "a3")):
                if new in best and ref in best:
                    common = sorted(set(per[new][0]) & set(per[ref][0]))
                    for k in common:
                        pooled[(lv, new, ref)].append((per[new][0][k][best[new][0]]["uho_pm"], per[ref][0][k][best[ref][0]]["uho_pm"]))
    R.w("")
    R.w("Unnecessary handovers at equal failure level, all site distances pooled")
    out = {}
    for (lv, new, ref), v in sorted(pooled.items()):
        a = np.array(v)
        c = paired(a[:, 0], a[:, 1])
        out["%s|%s|%s" % (lv, new, ref)] = c
        R.w("   level %s x budget, %s against %s: %s" % (rnd(lv, 2), new, ref, fmt_cmp(c)))
    R.data["S2_equal_failure"] = out
    R.data["S2_front"] = front
    return front


def section_sens(R, jobs):
    sel = [(j, res) for j, res, _, _ in jobs if j["stage"] == "S3"]
    if not sel:
        R.w("stage S3: not run")
        return None
    out = {}
    R.w("MemCHO against CHO and CHO against A3 with the frozen standard-budget settings (all conditions of a variant pooled)")
    R.w("%-10s %4s | %-44s | %-40s | %-34s" % ("variant", "n", "UHO: CHO -> MemCHO, rel. change [95 %], p", "failures: CHO -> MemCHO, diff", "prepared cells: CHO -> MemCHO"))
    for var in [v for v in study.SENS if any(j["variant"] == v for j, _ in sel)]:
        rr = [res for j, res in sel if j["variant"] == var]
        c = {k: paired(*pairs(rr, "memcho@std", "cho@std", k)) for k in ("uho_pm", "fail_pm", "prep_mean")}
        c["cho_a3_uho"] = paired(*pairs(rr, "cho@std", "a3@std", "uho_pm"))
        c["a3_fail"] = float(np.mean([r["a3@std"]["fail_pm"] for r in rr]))
        out[var] = c
        u = c["uho_pm"]
        rel_lo = 100.0 * u["ci_lo"] / u["mean_ref"] if u["mean_ref"] else float("nan")
        rel_hi = 100.0 * u["ci_hi"] / u["mean_ref"] if u["mean_ref"] else float("nan")
        R.w("%-10s %4d | %s -> %s, %s %% [%s, %s], p = %-8.2g | %s -> %s, %s [%s, %s] | %s -> %s" %
            (var, u["n"], rnd(u["mean_ref"], 3), rnd(u["mean_new"], 3), rnd(u["rel_pct"], 1), rnd(rel_lo, 1), rnd(rel_hi, 1), u["p"],
             rnd(c["fail_pm"]["mean_ref"], 4), rnd(c["fail_pm"]["mean_new"], 4), rnd(c["fail_pm"]["diff"], 4),
             rnd(c["fail_pm"]["ci_lo"], 4), rnd(c["fail_pm"]["ci_hi"], 4), rnd(c["prep_mean"]["mean_ref"], 3), rnd(c["prep_mean"]["mean_new"], 3)))
    R.data["S3"] = out
    return out


def section_windows(R, outdir, design):
    files = sorted(glob.glob(os.path.join(outdir, "events", "S1", "*.csv.gz")))
    if not files:
        R.w("no event logs")
        return
    d = study.DESIGNS[design]
    t0, t1 = d["discard"], d["t_sim"]
    edges = np.linspace(t0, t1, 4)
    cnt = defaultdict(lambda: np.zeros(3))
    for fn in files:
        with gzip.open(fn, "rt", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["outcome"] == "unnecessary":
                    b = min(int(np.searchsorted(edges, float(row["t_attempt"]), side="right")) - 1, 2)
                    cnt[row["rule"]][max(b, 0)] += 1
    umin = len(files) * d["n_ue"] * (t1 - t0) / 60.0 / 3.0
    R.w("Unnecessary handovers per UE-minute in the three thirds of the measured time (%d runs with event logs; exploratory)" % len(files))
    for rule in sorted(cnt):
        R.w("   %-12s %s" % (rule, "  ".join(rnd(x / umin, 3) for x in cnt[rule])))
    R.data["windows"] = {k: (v / umin).tolist() for k, v in cnt.items()}


def section_timing(R, jobs, design):
    if not jobs:
        return
    tot = defaultdict(lambda: [0.0, 0])
    for j, res, tm, wall in jobs:
        for n, r in res.items():
            a = tot[r["kind"] + (" (learning)" if n.split("@")[0].split("/")[0] in ("pum", "memcho") or n.startswith("mc_") else "")]
            a[0] += r["wall_s"]; a[1] += 1
    R.w("Engine seconds per rule-run (run length %g s): " % study.DESIGNS[design]["t_sim"] +
        "; ".join("%s %.1f (n = %d)" % (k, v[0] / v[1], v[1]) for k, v in sorted(tot.items())))
    mp = np.mean([tm.get("map_s", 0.0) for _, _, tm, _ in jobs]); rd = np.mean([tm.get("radio_s", 0.0) for _, _, tm, _ in jobs])
    en = np.mean([tm.get("engine_s", 0.0) for _, _, tm, _ in jobs])
    dev = sorted({tm.get("device", "?") + "/" + tm.get("backend", "?") for _, _, tm, _ in jobs})
    R.w("Per job: radio map %.1f s, radio samples %.1f s, engines %.1f s; share of the radio part %.1f %%; devices: %s" %
        (mp, rd, en, 100.0 * (mp + rd) / max(mp + rd + en, 1e-9), ", ".join(dev)))
    R.w("Sum of job wall times: %.2f h" % (sum(w for _, _, _, w in jobs) / 3600.0))
    R.data["timing"] = dict(per_rule={k: v[0] / v[1] for k, v in tot.items()}, map_s=float(mp), radio_s=float(rd), engine_s=float(en))


# ----------------------------------------------------------------------------
def _style(ax, xlabel="", ylabel="", title=""):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#c3c2b7")
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel(xlabel, color=INK2, fontsize=10)
    ax.set_ylabel(ylabel, color=INK2, fontsize=10)
    ax.set_title(title, color=INK, fontsize=11, loc="left")


def figures(outdir, S1, front, sens, tn):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:           # the tables do not depend on matplotlib
        return ["figures skipped: %r" % (e,)]
    made = []
    adir = os.path.join(outdir, "analysis")
    if S1:
        # 1 endpoints of the four main methods (one panel = one axis)
        eps = ENDPOINTS[:4]
        fig, axs = plt.subplots(1, len(eps), figsize=(3.3 * len(eps), 3.4), facecolor=SURFACE)
        for ax, (k, lab) in zip(axs, eps):
            ms = [m for m in MAIN if m + "@std" in S1["means"]]
            vals = [S1["means"][m + "@std"][k] for m in ms]
            bars = ax.bar(range(len(ms)), vals, width=0.62, color=[COLORS[m] for m in ms], edgecolor=SURFACE, linewidth=2)
            for b, v in zip(bars, vals):
                ax.text(b.get_x() + b.get_width() / 2, v, rnd(v, 3 if v < 10 else 2), ha="center", va="bottom", fontsize=9, color=INK)
            ax.set_xticks(range(len(ms)))
            ax.set_xticklabels([LABEL[m].replace("Per-user margin", "Per-user\nmargin") for m in ms], fontsize=9, color=INK2)
            _style(ax, title=lab)
        fig.suptitle("Main test, standard failure budget: means over all runs", x=0.01, ha="left", fontsize=12, color=INK)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(os.path.join(adir, "fig_endpoints.png"), dpi=160, facecolor=SURFACE); plt.close(fig)
        made.append("fig_endpoints.png")
        # 2 failure causes, stacked
        ms = [m for m in MAIN if m + "@std" in S1["means"]]
        fig, ax = plt.subplots(figsize=(7.6, 3.6), facecolor=SURFACE)
        left = np.zeros(len(ms))
        runs = S1["runs"]
        for (k, lab), col in zip(CAUSES, CAUSE_COLORS):
            v = np.array([np.mean([r[m + "@std"][k] for r in runs if m + "@std" in r]) for m in ms])
            ax.barh(range(len(ms)), v, left=left, height=0.55, color=col, edgecolor=SURFACE, linewidth=2, label=lab)
            left += v
        for i, t in enumerate(left):
            ax.text(t, i, "  " + rnd(t, 4), va="center", fontsize=9, color=INK)
        ax.set_yticks(range(len(ms))); ax.set_yticklabels([LABEL[m] for m in ms], color=INK2, fontsize=10)
        ax.invert_yaxis()
        _style(ax, xlabel="failures per UE-minute", title="Failures by cause, standard budget")
        ax.grid(axis="y", visible=False); ax.grid(axis="x", color=GRID, linewidth=0.8)
        ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22), labelcolor=INK2)
        fig.tight_layout()
        fig.savefig(os.path.join(adir, "fig_failure_causes.png"), dpi=160, facecolor=SURFACE); plt.close(fig)
        made.append("fig_failure_causes.png")
        # 3 per condition: MemCHO - CHO with intervals
        cells = S1["cells"]
        fig, axs = plt.subplots(1, 3, figsize=(11.5, 0.42 * len(cells) + 1.8), facecolor=SURFACE, sharey=True)
        for ax, (k, lab) in zip(axs, ENDPOINTS[:3]):
            for i, (isd, prof) in enumerate(cells):
                c = S1["percell"]["%d|%s|%s" % (isd, prof, k)]
                ax.plot([c["ci_lo"], c["ci_hi"]], [i, i], color=COLORS["memcho"], linewidth=2, solid_capstyle="round")
                ax.plot([c["diff"]], [i], marker="D", color=COLORS["memcho"], markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
            ax.axvline(0.0, color="#c3c2b7", linewidth=1)
            ax.set_yticks(range(len(cells))); ax.set_yticklabels(["%d m, %s" % c for c in cells], color=INK2, fontsize=9)
            _style(ax, xlabel="MemCHO - CHO", title=lab)
            ax.grid(axis="y", visible=False); ax.grid(axis="x", color=GRID, linewidth=0.8)
        axs[0].invert_yaxis()
        fig.suptitle("Paired difference per condition (mean and 95 % interval); left of zero = MemCHO lower", x=0.01, ha="left", fontsize=12, color=INK)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        fig.savefig(os.path.join(adir, "fig_conditions.png"), dpi=160, facecolor=SURFACE); plt.close(fig)
        made.append("fig_conditions.png")
    if front:
        isds = sorted({int(k.split("|")[0]) for k in front})
        fig, axs = plt.subplots(1, len(isds), figsize=(4.6 * len(isds), 4.6), facecolor=SURFACE, squeeze=False)
        for ax, isd in zip(axs[0], isds):
            for m in MAIN:
                pts = front.get("%d|%s" % (isd, m))
                if not pts:
                    continue
                x = np.array([p[2] for p in pts]); y = np.array([p[1] for p in pts])
                ax.scatter(x, y, s=22, marker=MARKS[m], color=COLORS[m], alpha=0.35, linewidths=0)
                order = np.lexsort((y, x))                  # lower envelope: best UHO at or below each failure rate
                env_x, env_y, best = [], [], np.inf
                for i in order:
                    if y[i] < best - 1e-12:
                        best = y[i]; env_x.append(x[i]); env_y.append(y[i])
                ax.step(env_x, env_y, where="post", color=COLORS[m], linewidth=2, label=LABEL[m], marker=MARKS[m], markersize=5,
                        markeredgecolor=SURFACE, markeredgewidth=1)
            if tn is not None:
                b = tn["isd"][str(isd)]["budget"]["std"]
                ax.axvline(b, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
                ax.text(b, ax.get_ylim()[1], " budget", color=MUTED, fontsize=8, va="top")
            _style(ax, xlabel="failures per UE-minute", ylabel="unnecessary handovers per UE-minute", title="site distance %d m" % isd)
            ax.grid(axis="x", color=GRID, linewidth=0.8)
        axs[0][0].legend(frameon=False, fontsize=9, labelcolor=INK2)
        fig.suptitle("All tuned settings on test seeds", x=0.01, ha="left", fontsize=12, color=INK)
        fig.text(0.01, 0.905, "point = one setting; line = lowest unnecessary-handover rate\nat or below a failure rate",
                 fontsize=8.5, color=INK2, va="top")
        fig.tight_layout(rect=(0, 0, 1, 0.84))
        fig.savefig(os.path.join(adir, "fig_frontier.png"), dpi=160, facecolor=SURFACE); plt.close(fig)
        made.append("fig_frontier.png")
    if sens:
        names = list(sens)
        fig, ax = plt.subplots(figsize=(7.4, 0.36 * len(names) + 1.6), facecolor=SURFACE)
        for i, v in enumerate(names):
            u = sens[v]["uho_pm"]
            if not u["mean_ref"]:
                continue
            lo, hi, mid = (100.0 * u[k] / u["mean_ref"] for k in ("ci_lo", "ci_hi", "diff"))
            ax.plot([lo, hi], [i, i], color=COLORS["memcho"], linewidth=2, solid_capstyle="round")
            ax.plot([mid], [i], marker="D", color=COLORS["memcho"], markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5)
            ax.text(hi, i, "  %s %%" % rnd(mid, 1), va="center", fontsize=8.5, color=INK)
        ax.axvline(0.0, color="#c3c2b7", linewidth=1)
        ax.set_yticks(range(len(names))); ax.set_yticklabels(names, color=INK2, fontsize=9)
        ax.invert_yaxis()
        _style(ax, xlabel="change of unnecessary handovers, MemCHO against CHO [%]", title="Sensitivities (frozen settings), mean and 95 % interval")
        ax.grid(axis="y", visible=False); ax.grid(axis="x", color=GRID, linewidth=0.8)
        fig.tight_layout()
        fig.savefig(os.path.join(adir, "fig_sensitivity.png"), dpi=160, facecolor=SURFACE); plt.close(fig)
        made.append("fig_sensitivity.png")
    return made


def write_runs_csv(outdir, jobs):
    keys = None
    with open(os.path.join(outdir, "analysis", "runs.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        for j, res, _, _ in jobs:
            for name, r in res.items():
                if keys is None:
                    keys = [k for k in r if k not in ("rule", "kind")]
                    wr.writerow(["stage", "env", "variant", "isd", "profile", "seed", "method", "rule"] + keys)
                wr.writerow([j["stage"], j["env"], j["variant"], j["isd"], j["profile"], j["seed"], j["method"], name] + [r.get(k, "") for k in keys])


def run(design="full"):
    """Analyse one design; returns the path of report.txt."""
    outdir = os.path.join(HERE, "results", design)
    os.makedirs(os.path.join(outdir, "analysis"), exist_ok=True)
    jobs = load(outdir)
    R = Report()
    R.w("Handover control in ultra-dense upper-mid-band networks: analysis of design '%s'" % design)
    if design != "full":
        R.w("THIS IS NOT THE STUDY. Design '%s' only shows that the pipeline runs; its numbers are not results." % design)
    R.h("0  Completeness")
    n_by = defaultdict(int)
    for j, _, _, _ in jobs:
        n_by[j["stage"]] += 1
    for st in study.STAGES:
        R.w("   %-3s %5d of %5d jobs finished" % (st, n_by[st], study.planned_count(st, design)[0]))
    fdir = os.path.join(outdir, "failed")
    failed = sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []
    R.w("   failed jobs: %d %s" % (len(failed), ", ".join(f[:-4] for f in failed[:30])))
    R.data["completeness"] = dict(done=dict(n_by), failed=[f[:-4] for f in failed])
    R.h("1  Tuning, street grid")
    tn = section_tuning(R, outdir, "grid")
    R.h("2  Main test S1 (street grid)")
    S1 = section_test(R, jobs, "S1", "S1", tn)
    R.h("3  Open area (nothing tied to place)")
    tno = section_tuning(R, outdir, "open")
    R.w("")
    section_test(R, jobs, "O3", "O3", tno)
    R.h("3b  Street grid without beam isolation, chi = 1 (stages X1-X3, added after the pilot; not part of H1)")
    tnx = section_tuning(R, outdir, "gridx")
    R.w("")
    section_test(R, jobs, "X3", "X3", tnx)
    R.h("4  S2: all tuned settings on test seeds, comparison at equal failure rate")
    front = section_frontier(R, jobs, tn)
    R.h("5  S3: sensitivities")
    sens = section_sens(R, jobs)
    R.h("6  Memory over time (exploratory)")
    section_windows(R, outdir, design)
    R.h("7  Run time")
    section_timing(R, jobs, design)
    write_runs_csv(outdir, jobs)
    made = figures(outdir, S1, front, sens, tn)
    R.h("8  Files")
    R.w("runs.csv (one row per run and rule), tuning_grid.csv, tuning_open.csv, report.json, figures: " + ", ".join(made))
    path = os.path.join(outdir, "analysis", "report.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(R.lines) + "\n")
    with open(os.path.join(outdir, "analysis", "report.json"), "w", encoding="utf-8") as f:
        json.dump(R.data, f, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--design", default="full", choices=sorted(study.DESIGNS))
    a = ap.parse_args()
    p = run(a.design)
    print("written:", p)
