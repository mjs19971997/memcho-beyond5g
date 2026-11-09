# -*- coding: utf-8 -*-
"""Path loss and LOS probability of 3GPP TR 38.901, Table 7.4.1-1 and 7.4.2-1.

Implemented: UMi street canyon and UMa, LOS and NLOS, for outdoor users.  The
formulas are specified for 0.5-100 GHz.  Their empirical basis between 7 and
24 GHz was thin when they were written; 3GPP studied that range again in
Release 19 (study item RP-234018), and published measurements at 6.75 and
16.95 GHz differ in part from the model.  Results at 7-15 GHz therefore carry
more model uncertainty than results at 3.5 GHz, and the study says so.

All functions take an ``ops`` back-end (see :mod:`bh6.backend`) so that the
same code runs with NumPy or PyTorch.  Distances in metres, frequency in GHz,
result in dB.
"""
import math

import numpy as np

from .backend import NumpyOps

C0 = 299792458.0
_NP = NumpyOps()


def breakpoint_distance(fc_ghz, h_bs, h_ut, h_e=1.0):
    """d'_BP = 4 h'_BS h'_UT f_c / c with effective heights h' = h - h_E."""
    return 4.0 * (h_bs - h_e) * (h_ut - h_e) * fc_ghz * 1e9 / C0


def pl_umi_los(d2d, fc_ghz, h_bs=10.0, h_ut=1.5, ops=_NP):
    """UMi street canyon, LOS (PL1 below the breakpoint, PL2 above)."""
    dh2 = (h_bs - h_ut) ** 2
    d3 = ops.sqrt(d2d * d2d + dh2)
    dbp = breakpoint_distance(fc_ghz, h_bs, h_ut)
    lf = 20.0 * math.log10(fc_ghz)
    pl1 = 32.4 + 21.0 * ops.log10(d3) + lf
    pl2 = 32.4 + 40.0 * ops.log10(d3) + lf - 9.5 * math.log10(dbp * dbp + dh2)
    return ops.where(d2d <= dbp, pl1, pl2)


def pl_umi_nlos(d2d, fc_ghz, h_bs=10.0, h_ut=1.5, ops=_NP):
    """UMi street canyon, NLOS: max(PL_LOS, PL'_NLOS)."""
    d3 = ops.sqrt(d2d * d2d + (h_bs - h_ut) ** 2)
    pln = 35.3 * ops.log10(d3) + 22.4 + 21.3 * math.log10(fc_ghz) - 0.3 * (h_ut - 1.5)
    return ops.maximum(pl_umi_los(d2d, fc_ghz, h_bs, h_ut, ops), pln)


def pl_uma_los(d2d, fc_ghz, h_bs=25.0, h_ut=1.5, ops=_NP):
    """UMa, LOS (effective environment height 1 m)."""
    dh2 = (h_bs - h_ut) ** 2
    d3 = ops.sqrt(d2d * d2d + dh2)
    dbp = breakpoint_distance(fc_ghz, h_bs, h_ut)
    lf = 20.0 * math.log10(fc_ghz)
    pl1 = 28.0 + 22.0 * ops.log10(d3) + lf
    pl2 = 28.0 + 40.0 * ops.log10(d3) + lf - 9.0 * math.log10(dbp * dbp + dh2)
    return ops.where(d2d <= dbp, pl1, pl2)


def pl_uma_nlos(d2d, fc_ghz, h_bs=25.0, h_ut=1.5, ops=_NP):
    """UMa, NLOS: max(PL_LOS, PL'_NLOS)."""
    d3 = ops.sqrt(d2d * d2d + (h_bs - h_ut) ** 2)
    pln = 13.54 + 39.08 * ops.log10(d3) + 20.0 * math.log10(fc_ghz) - 0.6 * (h_ut - 1.5)
    return ops.maximum(pl_uma_los(d2d, fc_ghz, h_bs, h_ut, ops), pln)


def path_loss(d2d, los, radio, ops=_NP):
    """Path loss for the model named in ``radio`` with a boolean LOS state."""
    if radio.pl_model == "umi":
        a = pl_umi_los(d2d, radio.fc_ghz, radio.h_bs, radio.h_ut, ops)
        b = pl_umi_nlos(d2d, radio.fc_ghz, radio.h_bs, radio.h_ut, ops)
    elif radio.pl_model == "uma":
        a = pl_uma_los(d2d, radio.fc_ghz, radio.h_bs, radio.h_ut, ops)
        b = pl_uma_nlos(d2d, radio.fc_ghz, radio.h_bs, radio.h_ut, ops)
    else:
        raise ValueError(radio.pl_model)
    return ops.where(los, a, b)


def p_los_umi(d2d):
    """LOS probability, UMi street canyon (Table 7.4.2-1), NumPy only."""
    d = np.maximum(np.asarray(d2d, dtype=float), 1e-9)
    return np.where(d <= 18.0, 1.0, 18.0 / d + np.exp(-d / 36.0) * (1.0 - 18.0 / d))


def p_los_uma(d2d, h_ut=1.5):
    """LOS probability, UMa (Table 7.4.2-1) for h_UT <= 13 m, NumPy only."""
    d = np.maximum(np.asarray(d2d, dtype=float), 1e-9)
    return np.where(d <= 18.0, 1.0, 18.0 / d + np.exp(-d / 63.0) * (1.0 - 18.0 / d))
