# -*- coding: utf-8 -*-
"""Figures of the third paper, drawn from the result files of the finished study.

Sources: results/full_i9/results/full/analysis/report.json and runs.csv, data/p3.json (derive.py), calibration.json,
and the simulator itself for the drawing of the street grid.  Run derive.py first.

    python p3_figs.py
"""
import csv, json, os, sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figstyle import WF, INK, MUTE, LIGHT, OI, METH, LAB, COL, MK, style, panel, newfig, savefig

HERE = os.path.dirname(os.path.abspath(__file__))
G6 = os.path.dirname(HERE)
ANA = next(p for p in (os.path.join(G6, "results", "full", "analysis"), os.path.join(G6, "results", "full_i9", "results", "full", "analysis")) if os.path.isdir(p))
R = json.load(open(os.path.join(ANA, "report.json"), encoding="utf-8"))
D = json.load(open(os.path.join(HERE, "data", "p3.json"), encoding="utf-8"))
sys.path.insert(0, G6)

COND = [(d, p) for d in (50, 100, 150) for p in ("ped", "veh8", "veh16")]
PLAB = dict(ped="ped.", veh8="8 m/s", veh16="16 m/s")
SENS_ORDER = [
    ("Radio", ["fc7", "fc15", "chi010", "chi100", "noclutter", "place50", "place0", "dyn3", "meas2"]),
    ("Protocol", ["prep20", "prep100", "t310_05", "t310_2", "reest03"]),
    ("Users", ["veh30", "mix", "ue30", "ue120", "hot50"]),
    ("Input to the memory", ["pos5", "pos15", "head05"]),
    ("Run length", ["long"]),
]
SENS_LAB = dict(fc7="carrier 7 GHz", fc15="carrier 15 GHz", chi010=r"beam isolation $\chi$ = 0.1", chi100=r"no beam isolation, $\chi$ = 1",
                noclutter="no in-street obstacles", place50="half of shadowing tied to place", place0="no shadowing tied to place",
                dyn3="time-varying part 3 dB", meas2="L1 sample error 2 dB", prep20="preparation 20 ms", prep100="preparation 100 ms",
                t310_05="T310 = 0.5 s", t310_2="T310 = 2 s", reest03="re-establishment 0.3 s", veh30="vehicles at 30 m/s",
                mix="mixed population", ue30="30 users", ue120="120 users", hot50="half of the cells hotspots",
                pos5="position error 5 m", pos15="position error 15 m", head05="heading error 0.5 rad", long="runs three times as long")


def fmt_axis_pct(ax):
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.0f}" if v else "0"))


# ------------------------------------------------------------------------------------------------ 1 scheme
def fig_scheme():
    Wm, Hm = 165.0, 62.0
    fig = plt.figure(figsize=(Wm / 25.4, Hm / 25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, Wm); ax.set_ylim(0, Hm); ax.axis("off")

    def box(x, y, w, h, fc, head, lines, hc=INK):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=1.5", fc=fc, ec="#3c3c3c", lw=0.6, zorder=2))
        ax.text(x + w / 2, y + h - 3.2, head, ha="center", va="center", fontsize=7.8, weight="bold", color=hc, zorder=3)
        ax.text(x + 2.0, y + h - 7.0, lines, ha="left", va="top", fontsize=6.9, color=INK, zorder=3, linespacing=1.38)

    def arrow(p, q, col="#3c3c3c", ls="-", lw=0.9, cs="arc3"):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=7, lw=lw, color=col, zorder=4, ls=ls,
                                     connectionstyle=cs, shrinkA=0, shrinkB=0))

    G, B, O = "#f1f1f1", "#e3eef8", "#fbe6d9"
    y0, h = 21.0, 33.0
    box(2, y0, 29, h, G, "UE measures", "L1 sample every 40 ms\nL3 filter ($k$ = 4)\nreports neighbour $n$ when\n$F_n - F_s > O_{\\mathrm{rep}}$\n+ reported position and\nheading (10 m bins)")
    box(35, y0, 38, h, B, "Place memory", "key: 10 m square $\\times$\nheading quadrant $\\times$ target\ncounts: useful, unnecessary,\nearly / wrong cell, late\nforgetting $\\tau$ = 600 s,\nshrunk to the cell pair\n$\\Rightarrow\\ \\Delta\\mathrm{bad}(u,n),\\ \\mathrm{late}(u,n)$")
    box(35, 2, 38, 15, G, "Motion", "3 s sector ahead of the user\n$\\Rightarrow$ overlap $\\mathrm{ovl}(u,n)$")
    box(77, y0, 44, h, O, "Offsets per user and target",
        "$O_{\\mathrm{prep}} = o_{\\mathrm{prep}} + v_U\\Delta\\mathrm{bad} - v_L\\,\\mathrm{late} - v_A\\,\\mathrm{ovl}$\n"
        "$O_{\\mathrm{exec}} = o_{\\mathrm{exec}} + w_U\\Delta\\mathrm{bad} - w_L\\,\\mathrm{late} - w_A\\,\\mathrm{ovl}$\n\n"
        "prepare $n$ if $F_n - F_s \\geq O_{\\mathrm{prep}}$\nand $n$ is among the $n_{\\max}$ best;\n"
        "$O_{\\mathrm{exec}}$ goes into the conditional\nconfiguration (Rel-16 field)")
    box(125, y0, 38, h, G, "UE executes", "on its own when\n$F_n - F_s > O_{\\mathrm{exec}}(u,n)$\nfor $T_{\\mathrm{exec}}$; the other\nprepared cells are released\n\nafter the stay: outcome label\n(useful, unnecessary, ...)")
    arrow((31, y0 + h / 2), (35, y0 + h / 2)); arrow((73, y0 + h / 2), (77, y0 + h / 2)); arrow((121, y0 + h / 2), (125, y0 + h / 2))
    arrow((73, 9.5), (99, y0), cs="angle,angleA=0,angleB=90,rad=0")
    arrow((16.5, y0), (35, 9.5), cs="angle,angleA=-90,angleB=180,rad=0")
    ax.plot([144, 144, 54], [y0 + h, y0 + h + 4.5, y0 + h + 4.5], color=OI["red"], lw=1.0, zorder=4)
    arrow((54, y0 + h + 4.5), (54, y0 + h), col=OI["red"], lw=1.0)
    ax.text(99, y0 + h + 5.3, "outcome of every attempt and every late failure is written back under the place where it was decided",
            ha="center", va="bottom", fontsize=6.9, color=OI["red"])
    ax.text(144, 10.0, "all weights 0 $\\Rightarrow$ standard CHO\n(checked on event logs)", ha="center", va="center", fontsize=6.9, color=MUTE)
    savefig(fig, "fig_scheme")


# ------------------------------------------------------------------------------------------------ 2 scenario
def fig_scenario():
    from bh6.layout import grid_layout
    from bh6.params import Scenario
    from bh6.mobility import gen_traj
    L = grid_layout(100.0)
    fig, axs = newfig(165, 62, 1, 2, gridspec_kw=dict(width_ratios=[1.72, 1.0]))
    ax = axs[0]
    for b in L.buildings:
        ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fc="#d9d9d9", ec="none", zorder=1))
    sc = Scenario(isd=100.0, profile="veh16", n_ue=6, t_sim=60.0, seed=3)
    X, Y, V, TH = gen_traj(L, sc, np.random.default_rng(5))
    cols = [OI["blue"], OI["red"], OI["green"], OI["orange"], OI["purple"], OI["sky"]]
    for u in range(X.shape[1]):
        ax.plot(X[:, u], Y[:, u], color=cols[u], lw=0.9, zorder=3)
        ax.plot(X[-1, u], Y[-1, u], marker=">", ms=0, color=cols[u])
    ax.scatter(L.sites[:, 0], L.sites[:, 1], s=7, marker="^", color=INK, zorder=4, lw=0)
    ax.set_aspect("equal"); ax.set_xlim(L.xmin - 5, L.xmax + 5); ax.set_ylim(L.ymin - 5, L.ymax + 5)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    panel(ax, "a", f"street grid, sites every 100 m ({L.M} sites), paths of six users in 60 s")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    # (b) place bins around an intersection
    ax = axs[1]
    x0, x1, y0, y1 = -10 - 60, -10 + 70, -50, 60
    for b in L.buildings:
        ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fc="#d9d9d9", ec="none", zorder=1))
    for gx in np.arange(-80, 80, 10.0):
        ax.plot([gx, gx], [y0, y1], color="#c8c8c8", lw=0.3, zorder=0.5)
    for gy in np.arange(-60, 70, 10.0):
        ax.plot([x0, x1], [gy, gy], color="#c8c8c8", lw=0.3, zorder=0.5)
    s = L.sites[(L.sites[:, 0] > x0) & (L.sites[:, 0] < x1) & (L.sites[:, 1] > y0) & (L.sites[:, 1] < y1)]
    ax.scatter(s[:, 0], s[:, 1], s=16, marker="^", color=INK, zorder=4, lw=0)
    ax.add_patch(Rectangle((20, 0), 10, 10, fc=OI["red"], alpha=0.35, ec=OI["red"], lw=0.6, zorder=2))
    ax.annotate("", xy=(48, 6.5), xytext=(8, 6.5), arrowprops=dict(arrowstyle="-|>", color=OI["blue"], lw=1.0, mutation_scale=7), zorder=5)
    ax.annotate("", xy=(2, 2.5), xytext=(48, 2.5), arrowprops=dict(arrowstyle="-|>", color=OI["green"], lw=1.0, mutation_scale=7), zorder=5)
    ax.text(25, 16, "one square, two keys:\neastbound and westbound\nare counted apart", fontsize=6.9, ha="center", va="bottom", color=INK)
    ax.set_aspect("equal"); ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
    ax.set_xlabel("x [m]")
    panel(ax, "b", "10 m place bins at a crossing")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    savefig(fig, "fig_scenario")


# ------------------------------------------------------------------------------------------------ 3 main endpoints
def fig_main():
    fig, axs = newfig(165, 60, 1, 4, sharey=True)
    rows = METH[::-1]
    ypos = {m: i + (0 if i < 5 else 0.6) for i, m in enumerate(rows)}
    spec = [("uho_pm", 1, "unnecessary HO per UE-min", "a"), ("fail_pm", 1000, r"failures per UE-min ($\times10^{-3}$)", "b"),
            ("prep_mean", 1, "mean prepared cells", "c"), ("delivered", 100, "delivered share of demand [%]", "d")]
    for ax, (k, sc, lab, let) in zip(axs, spec):
        style(ax, "x")
        for m in rows:
            c = D["ci"][f"S1|{m}@std"][k]
            ax.errorbar(c["mean"] * sc, ypos[m], xerr=[[(c["mean"] - c["lo"]) * sc], [(c["hi"] - c["mean"]) * sc]], fmt=MK[m],
                        color=COL[m], ms=4, lw=0.9, capsize=1.5, zorder=3, mec="white" if m != "mc_mot" else None, mew=0.3)
        cm = D["ci"]["S1|cho@std"][k]["mean"] * sc
        ax.axvline(cm, color=COL["cho"], lw=0.6, ls=(0, (3, 2)), zorder=1)
        ax.set_xlabel(lab)
        panel(ax, let)
    axs[0].set_yticks([ypos[m] for m in rows]); axs[0].set_yticklabels([LAB[m] for m in rows])
    axs[0].axhline(4.8, color=LIGHT, lw=0.5)
    for t in axs[0].get_yticklabels():
        if t.get_text() == "MemCHO": t.set_weight("bold")
    savefig(fig, "fig_main")


# ------------------------------------------------------------------------------------------------ 4 per condition
def fig_conditions():
    fig, axs = newfig(165, 58, 1, 2)
    x = np.arange(len(COND))
    for ax, (k, sc, lab, let) in zip(axs, [("uho_pm", 1, "MemCHO $-$ CHO, unnecessary HO per UE-min", "a"),
                                          ("fail_pm", 1000, r"MemCHO $-$ CHO, failures per UE-min ($\times10^{-3}$)", "b")]):
        style(ax, "y")
        for off, src, col, mk, name in ((-0.15, "S1_percell", OI["red"], "o", r"beam isolation $\chi$ = 0.3 (main test, 40 seeds)"),
                                         (0.15, "X3_percell", OI["blue"], "s", r"no isolation $\chi$ = 1 (added after pilot, 20 seeds)")):
            v = [R[src][f"{d}|{p}|{k}"] for d, p in COND]
            ax.errorbar(x + off, [q["diff"] * sc for q in v], yerr=[[(q["diff"] - q["ci_lo"]) * sc for q in v], [(q["ci_hi"] - q["diff"]) * sc for q in v]],
                        fmt=mk, color=col, ms=3.6, lw=0.8, capsize=1.4, label=name, zorder=3, mec="white", mew=0.3)
        ax.axhline(0, color=INK, lw=0.6)
        for b in (2.5, 5.5):
            ax.axvline(b, color=LIGHT, lw=0.5)
        ax.set_xticks(x); ax.set_xticklabels([f"{PLAB[p]}" for d, p in COND])
        for i, d in enumerate((50, 100, 150)):
            ax.text(1 + 3 * i, 1.0, f"{d} m", transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=7.5, color=MUTE)
        ax.set_ylabel(lab)
        panel(ax, let)
    axs[0].legend(loc="lower left", fontsize=7)
    savefig(fig, "fig_conditions")


# ------------------------------------------------------------------------------------------------ 5 failure causes
def fig_causes():
    rows = list(csv.DictReader(open(os.path.join(ANA, "runs.csv"), encoding="utf-8")))
    causes = [("f_late_cmd_pm", "command lost (too late)", OI["orange"]), ("f_late_prep_pm", "link failure during preparation", OI["yellow"]),
              ("f_late_rlf_pm", "link failure, no handover started", OI["red"]), ("f_exec_fail_pm", "execution failure", OI["blue"]),
              ("f_early_rlf_pm", "failure soon after handover", OI["sky"]), ("f_cov_rlf_pm", "coverage", LIGHT)]
    meths = ["a3", "pum", "cho", "memcho"]
    sel0 = [r for r in rows if r["stage"] in ("S1", "X3") and r["rule"].split("@")[0] in meths and r["rule"].endswith("@std")]
    causes = [c for c in causes if sum(float(r[c[0]]) for r in sel0) > 0]      # causes that never occur are left out
    fig, axs = newfig(165, 42, 1, 2)
    for ax, stg, let, title in ((axs[0], "S1", "a", r"street grid, $\chi$ = 0.3 (main test)"), (axs[1], "X3", "b", r"street grid, $\chi$ = 1")):
        style(ax, "x")
        for i, m in enumerate(meths[::-1]):
            sel = [r for r in rows if r["stage"] == stg and r["rule"] == f"{m}@std"]
            left = 0.0
            for k, name, c in causes:
                v = 1000 * np.mean([float(r[k]) for r in sel])
                ax.barh(i, v, left=left, color=c, height=0.62, ec="white", lw=0.3, label=name if (stg == "S1" and i == 0) else None, zorder=3)
                left += v
        ax.set_yticks(range(4)); ax.set_yticklabels([LAB[m] for m in meths[::-1]])
        ax.set_xlabel(r"failures per UE-min ($\times10^{-3}$)")
        panel(ax, let, title)
    fig.legend(loc="outside lower center", ncol=3, fontsize=7)
    savefig(fig, "fig_causes")


# ------------------------------------------------------------------------------------------------ 6 equal failure level (S2)
def fig_frontier():
    fig, axs = newfig(165, 56, 1, 3)
    for ax, d, let in zip(axs, (50, 100, 150), "abc"):
        style(ax, "both")
        bud = R["tuning_grid"][str(d)]["budget"]["std"]
        for m in ("a3", "pum", "cho", "memcho"):
            pts = np.array([[q[2] * 1000, q[1]] for q in R["S2_front"][f"{d}|{m}"]])
            ax.scatter(pts[:, 0], pts[:, 1], s=6, marker=MK[m], color=COL[m], alpha=0.35, lw=0, zorder=2)
            o = pts[np.argsort(pts[:, 0])]
            env = [o[0]]
            for p in o[1:]:
                if p[1] < env[-1][1]:
                    env.append(p)
            env = np.array(env)
            ax.step(env[:, 0], env[:, 1], where="post", color=COL[m], lw=1.1, zorder=3, label=LAB[m])
        ax.axvline(bud * 1000, color=MUTE, lw=0.6, ls=(0, (3, 2)))
        ax.text(bud * 1000, 0.98, " budget", transform=ax.get_xaxis_transform(), fontsize=6.8, color=MUTE, va="top")
        ax.set_xscale("symlog", linthresh=1.0); ax.set_xlim(-0.05, 300)
        ax.set_ylim(0, 2.0)
        ax.set_xlabel(r"failures per UE-min ($\times10^{-3}$)")
        panel(ax, let, f"site distance {d} m")
    axs[0].set_ylabel("unnecessary HO per UE-min")
    h = [Line2D([], [], color=COL[m], marker=MK[m], lw=1.1, ms=3.5, label=LAB[m]) for m in ("a3", "pum", "cho", "memcho")]
    fig.legend(handles=h, loc="outside lower center", ncol=4, fontsize=7)
    savefig(fig, "fig_frontier")


# ------------------------------------------------------------------------------------------------ 7 memory over time
def fig_time():
    W = D["windows"]
    e = np.array(W["edges"]); mid = (e[:-1] + e[1:]) / 2 / 60.0
    fig, ax = newfig(110, 52)
    style(ax, "y")
    for m in ("pum", "a3", "cho", "memcho"):
        ax.plot(mid, W["rate"][f"{m}@std"], marker=MK[m], color=COL[m], label=LAB[m], ms=3.8, mec="white", mew=0.3)
    ax.set_xlabel("time in the run [min] (memory empty at 0)"); ax.set_ylabel("unnecessary HO per UE-min")
    ax.set_xlim(0, 11.5); ax.set_ylim(0, None)
    ax.legend(loc="lower center", fontsize=7, ncol=4)
    savefig(fig, "fig_time")


# ------------------------------------------------------------------------------------------------ 8 sensitivities
def fig_sens():
    S3, B = R["S3"], D["s3_base"]
    items = [("ref", "reference: main settings")] + [(v, SENS_LAB[v]) for _, vs in SENS_ORDER for v in vs]
    fig, axs = newfig(165, 104, 1, 2, sharey=True, gridspec_kw=dict(width_ratios=[1.25, 1.0]))
    y = []; yy = 0.0; grp = []
    for i, (k, _) in enumerate(items):
        if i == 1 or k in [vs[0] for _, vs in SENS_ORDER[1:]]:
            yy += 0.6
        y.append(-yy); yy += 1
    for k, lab in [(vs[0], g) for g, vs in SENS_ORDER]:
        grp.append((y[[q[0] for q in items].index(k)], lab))
    for ax, let, kind in ((axs[0], "a", "uho"), (axs[1], "b", "fail")):
        style(ax, "x")
        for (k, lab), yv in zip(items, y):
            if kind == "uho":
                if k == "ref":
                    m, lo, hi = B["rel_pct"], B["rel_lo"], B["rel_hi"]
                else:
                    q = S3[k]["uho_pm"]; m, lo, hi = q["rel_pct"], 100 * q["ci_lo"] / q["mean_ref"], 100 * q["ci_hi"] / q["mean_ref"]
            else:
                if k == "ref":
                    q = B["fail_diff"]; m, lo, hi = 1000 * q["mean"], 1000 * q["lo"], 1000 * q["hi"]
                else:
                    q = S3[k]["fail_pm"]; m, lo, hi = 1000 * q["diff"], 1000 * q["ci_lo"], 1000 * q["ci_hi"]
            worse = lo > 0
            col = OI["blue"] if worse else (OI["red"] if hi < 0 else MUTE)
            ax.errorbar(m, yv, xerr=[[m - lo], [hi - m]], fmt="o" if k != "ref" else "D", color=col, ms=3.4, lw=0.8, capsize=1.3, zorder=3,
                        mec="white", mew=0.3)
        ax.axvline(0, color=INK, lw=0.6)
    axs[0].set_yticks(y); axs[0].set_yticklabels([lab for _, lab in items])
    for yv, g in grp:
        axs[0].text(-0.02, yv + 0.75, g, transform=axs[0].get_yaxis_transform(), ha="right", va="center", fontsize=7.2, style="italic", color=MUTE)
    axs[0].set_xlabel("MemCHO against CHO: unnecessary HO, change [%]")
    axs[1].set_xlabel(r"MemCHO $-$ CHO: failures per UE-min ($\times10^{-3}$)")
    panel(axs[0], "a"); panel(axs[1], "b")
    savefig(fig, "fig_sens")


# ------------------------------------------------------------------------------------------------ 9 calibration
def fig_calib():
    A = D["calib"]["partA"]
    fig, axs = newfig(165, 54, 1, 3)
    for ax, i, lab, let in ((axs[0], 0, "handovers per UE-min", "a"), (axs[1], 1, "unnecessary HO per UE-min", "b"), (axs[2], 2, "failures per UE-min", "c")):
        style(ax, "both")
        ns = np.array([a["ns3"][i] for a in A]); sm = np.array([a["sim"][i] for a in A])
        tt = np.array([a["ttt"] for a in A])
        for t, mk, c in ((100, "o", OI["blue"]), (300, "s", OI["green"]), (500, "^", OI["orange"]), (1000, "D", OI["red"])):
            s = tt == t
            ax.scatter(ns[s], sm[s], marker=mk, color=c, s=12, lw=0.3, ec="white", zorder=3, label=f"TTT {t} ms")
        hi = max(ns.max(), sm.max()) * 1.05
        ax.plot([0, hi], [0, hi], color=MUTE, lw=0.6, ls=(0, (3, 2)))
        ax.set_xlim(0, hi); ax.set_ylim(0, hi); ax.set_aspect("equal")
        ax.set_xlabel("ns-3 / 5G-LENA"); ax.set_ylabel("this simulator" if let == "a" else "")
        panel(ax, let, lab)
    axs[0].legend(loc="upper left", fontsize=6.8, handletextpad=0.1)
    savefig(fig, "fig_calib")


if __name__ == "__main__":
    which = sys.argv[1:] or ["scheme", "scenario", "main", "conditions", "causes", "frontier", "time", "sens", "calib"]
    for w in which:
        globals()["fig_" + w]()
