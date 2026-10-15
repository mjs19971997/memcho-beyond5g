# -*- coding: utf-8 -*-
"""Figure style of the third paper (adapted from code/figstyle8.py of the earlier papers).

Every figure is drawn at its print width (the text width of the single-column manuscript is 165 mm), so the type
inside is 7-8 pt in print, the size of the caption text.  Output: vector PDF (fonts embedded), SVG and 600-dpi PNG.
Colours: the Okabe-Ito palette, which stays distinguishable for the common forms of colour-vision deficiency;
every series also has its own marker, so the figures read in grey scale as well.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

WF = 165 / 25.4          # text width [in]

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 8.0, "axes.labelsize": 8.0, "axes.titlesize": 8.0,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.linewidth": 0.6, "axes.edgecolor": "#3c3c3c", "axes.labelcolor": "#111111",
    "xtick.color": "#3c3c3c", "ytick.color": "#3c3c3c",
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "lines.linewidth": 1.2, "lines.markersize": 4.0,
    "grid.color": "#dcdcdc", "grid.linewidth": 0.5,
    "legend.frameon": False,
    "figure.dpi": 150,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "svg.fonttype": "path",
    "axes.unicode_minus": True,
})

INK, MUTE, LIGHT = "#111111", "#5a5a5a", "#bdbdbd"
# Okabe-Ito
OI = dict(orange="#E69F00", sky="#56B4E9", green="#009E73", yellow="#F0E442", blue="#0072B2", red="#D55E00", purple="#CC79A7", black="#000000")
METH = ["a3", "pum", "cho", "memcho", "mc_exec", "mc_prep", "mc_mem", "mc_mot", "mc_pair"]
LAB = dict(a3="A3", pum="Per-user margin", cho="CHO", memcho="MemCHO", mc_exec="Execution only", mc_prep="Preparation only",
           mc_mem="Memory only", mc_mot="Motion only", mc_pair="Cell-pair memory")
COL = dict(a3=OI["orange"], pum=OI["purple"], cho=OI["blue"], memcho=OI["red"], mc_exec=OI["green"], mc_prep=OI["sky"],
           mc_mem="#7f7f7f", mc_mot=OI["black"], mc_pair="#8c6d31")
MK = dict(a3="s", pum="D", cho="^", memcho="o", mc_exec="v", mc_prep="<", mc_mem=">", mc_mot="X", mc_pair="P")


def style(ax, grid="y"):
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    if grid:
        ax.grid(axis=grid, zorder=0)
    ax.set_axisbelow(True)


def panel(ax, letter, title=""):
    ax.set_title(f"({letter}) {title}".rstrip(), loc="left", pad=3)


def newfig(w_mm, h_mm, nrows=1, ncols=1, **kw):
    fig, ax = plt.subplots(nrows, ncols, figsize=(w_mm / 25.4, h_mm / 25.4), layout="constrained", **kw)
    fig.get_layout_engine().set(w_pad=0.02, h_pad=0.03, wspace=0.04, hspace=0.05)
    return fig, ax


def savefig(fig, name):
    for ext, kw in (("pdf", {}), ("svg", {}), ("png", {"dpi": 600})):
        fig.savefig(os.path.join(FIGDIR, f"{name}.{ext}"), facecolor="white", **kw)
    plt.close(fig)
    print("saved", name)
