# -*- coding: utf-8 -*-
"""Paired statistics used by the analysis.

* exact two-sided Wilcoxon signed-rank test (zero differences dropped, ties get
  mid-ranks, the exact null distribution is built for the ranks actually present);
* mean paired difference with a 95 % t interval;
* Holm correction for a family of tests;
* decimal rounding, half away from zero, for printed rates.
"""
import math
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
from scipy import stats as _st

TIE_TOL = 1e-9       # differences closer than this count as equal (rates are ratios of small integers)


def wilcoxon_exact(d):
    """Exact two-sided p-value of the Wilcoxon signed-rank test for paired differences ``d``.

    Returns ``(p, n_used, w_plus)``; ``p`` is 1.0 if all differences are zero.
    """
    d = np.asarray(d, dtype=float)
    d = d[np.abs(d) > TIE_TOL]
    n = len(d)
    if n == 0:
        return 1.0, 0, 0.0
    a = np.abs(d)
    order = np.argsort(a, kind="mergesort")
    ranks2 = np.empty(n, dtype=np.int64)             # twice the mid-rank, an integer
    i = 0
    while i < n:
        j = i
        while j + 1 < n and a[order[j + 1]] - a[order[i]] <= TIE_TOL:
            j += 1
        ranks2[order[i:j + 1]] = (i + 1) + (j + 1)   # 2 * mean of ranks i+1 .. j+1
        i = j + 1
    total = int(ranks2.sum())
    p = np.zeros(total + 1)
    p[0] = 1.0
    for r in ranks2:                                  # each rank joins the positive sum with probability 1/2
        q = 0.5 * p
        q[r:] += 0.5 * p[:-r]
        p = q
    w = int(ranks2[d > 0].sum())
    lo = p[:w + 1].sum()
    hi = p[w:].sum()
    return float(min(1.0, 2.0 * min(lo, hi))), n, w / 2.0


def paired(a, b):
    """Summary of the paired comparison ``a`` (new) against ``b`` (reference).

    Returns a dict with the means, the mean difference a - b, its 95 % t
    interval, the relative change in per cent and the exact Wilcoxon p-value.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = a - b
    n = len(d)
    m = float(d.mean()) if n else float("nan")
    if n > 1:
        se = float(d.std(ddof=1) / math.sqrt(n))
        h = float(_st.t.ppf(0.975, n - 1) * se)
    else:
        h = float("nan")
    p, n_used, _ = wilcoxon_exact(d)
    mb = float(b.mean()) if n else float("nan")
    return dict(n=n, mean_new=float(a.mean()) if n else float("nan"), mean_ref=mb, diff=m, ci_lo=m - h, ci_hi=m + h,
                rel_pct=(100.0 * m / mb) if n and abs(mb) > 1e-12 else float("nan"), p=p, n_nonzero=n_used)


def holm(pvals):
    """Holm-adjusted p-values in the original order."""
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.empty(len(p))
    run = 0.0
    for k, i in enumerate(order):
        run = max(run, (len(p) - k) * p[i])
        adj[i] = min(1.0, run)
    return adj.tolist()


def rnd(x, nd=3):
    """Decimal rounding, half away from zero, as a string (no binary rounding surprises)."""
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "n/a"
    q = Decimal(1).scaleb(-nd)
    return str(Decimal(repr(float(x))).quantize(q, rounding=ROUND_HALF_UP))
