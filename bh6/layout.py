# -*- coding: utf-8 -*-
"""Deployment geometry: street grid with buildings, or an open area.

Street grid: the urban grid of 3GPP TR 37.885 (Annex A): intersections every
433 m (x) and 250 m (y), streets 20 m wide, the space between the streets
filled by building blocks.  The area is 2 x 2 blocks with three east-west and
three north-south streets.  Sites stand on the pavement along the streets, one
every ``isd`` metres, alternately on the two sides.  A link has a line of sight
if the straight line between site and user crosses no building block.

Open area: the same rectangle without buildings, sites on a hexagonal grid.
"""
from dataclasses import dataclass

import numpy as np

from .backend import NumpyOps

_NP = NumpyOps()
PITCH = (433.0, 250.0)
STREET_W = 20.0


@dataclass
class Layout:
    env: str
    sites: np.ndarray        # (M, 2) site positions [m]
    buildings: np.ndarray    # (B, 4) rectangles x0, y0, x1, y1 [m]
    xs: np.ndarray           # x of the north-south street centre lines
    ys: np.ndarray           # y of the east-west street centre lines
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @property
    def M(self):
        return len(self.sites)

    def street_mask(self, x, y, margin=0.0):
        """True where the point lies in a street (grid) or in the area (open)."""
        if self.env != "grid":
            return np.ones(np.broadcast(x, y).shape, dtype=bool)
        hw = STREET_W / 2.0 + margin
        in_x = (np.abs(np.asarray(x)[..., None] - self.xs) <= hw).any(-1)
        in_y = (np.abs(np.asarray(y)[..., None] - self.ys) <= hw).any(-1)
        return in_x | in_y


def _along(length, isd):
    """Positions along a street of the given length, spacing ``isd``, centred."""
    n = max(1, int(round(length / isd)))
    return (np.arange(n) - (n - 1) / 2.0) * isd


def grid_layout(isd=100.0, nbx=2, nby=2, site_offset=9.0, sites=None):
    """Street grid of ``nbx`` x ``nby`` blocks centred on the origin.

    ``sites``: explicit list of site positions; otherwise sites are placed every
    ``isd`` metres along every street (a north-south site closer than 0.4 isd
    to an east-west site is left out, so intersections are not doubled).
    """
    px, py = PITCH
    xs = (np.arange(nbx + 1) - nbx / 2.0) * px
    ys = (np.arange(nby + 1) - nby / 2.0) * py
    hw = STREET_W / 2.0
    b = [(xs[i] + hw, ys[j] + hw, xs[i + 1] - hw, ys[j + 1] - hw) for i in range(nbx) for j in range(nby)]
    if sites is None:
        pts = []
        for j, y in enumerate(ys):                       # east-west streets
            for i, s in enumerate(_along(xs[-1] - xs[0], isd)):
                side = 1.0 if (i + j) % 2 == 0 else -1.0
                pts.append((s, y + side * site_offset))
        ew = np.array(pts)
        for i, x in enumerate(xs):                       # north-south streets
            for j, s in enumerate(_along(ys[-1] - ys[0], isd)):
                side = 1.0 if (i + j) % 2 == 0 else -1.0
                p = (x + side * site_offset, s)
                if np.min(np.hypot(ew[:, 0] - p[0], ew[:, 1] - p[1])) >= 0.4 * isd:
                    pts.append(p)
        sites = np.array(pts)
    else:
        sites = np.asarray(sites, dtype=float)
    return Layout("grid", sites, np.array(b), xs, ys, xs[0] - hw, xs[-1] + hw, ys[0] - hw, ys[-1] + hw)


def open_layout(isd=100.0, size=(886.0, 520.0)):
    """Open rectangle of the same size as the street grid, hexagonal site grid."""
    w, h = size
    dy = isd * np.sqrt(3.0) / 2.0
    ny = int(h / dy) + 1
    nx = int(w / isd) + 1
    pts = []
    for j in range(ny):
        y = (j - (ny - 1) / 2.0) * dy
        if j % 2 == 0:
            xs = (np.arange(nx) - (nx - 1) / 2.0) * isd
        else:                                    # odd rows are shifted by half a site distance
            xs = (np.arange(nx - 1) - (nx - 2) / 2.0) * isd
        pts.extend((x, y) for x in xs)
    return Layout("open", np.array(pts), np.zeros((0, 4)), np.array([]), np.array([]),
                  -w / 2.0, w / 2.0, -h / 2.0, h / 2.0)


def make_layout(sc):
    """Layout of a scenario."""
    if sc.env == "grid":
        return grid_layout(sc.isd, site_offset=sc.site_offset, sites=sc.sites)
    if sc.env == "open":
        return open_layout(sc.isd)
    raise ValueError(sc.env)


def los_matrix(px, py, sites, buildings, ops=_NP, block=200000):
    """Line of sight between points and sites.

    ``px``, ``py``: (P,) point coordinates.  Returns a boolean array (P, M):
    True if the segment site -> point crosses no rectangle of ``buildings``
    (slab method; a segment that only touches an edge is not blocked).
    """
    px = np.asarray(px, dtype=float)
    py = np.asarray(py, dtype=float)
    P, M = len(px), len(sites)
    res = np.ones((P, M), dtype=bool)
    if len(buildings) == 0 or P == 0:
        return res
    sx = ops.arr(sites[:, 0])[None, :]
    sy = ops.arr(sites[:, 1])[None, :]
    tiny = 1e-9
    for a in range(0, P, block):
        qx = ops.arr(px[a:a + block])[:, None]
        qy = ops.arr(py[a:a + block])[:, None]
        dx = qx - sx
        dy = qy - sy
        dx = ops.where(ops.abs(dx) < tiny, tiny, dx)
        dy = ops.where(ops.abs(dy) < tiny, tiny, dy)
        blocked = None
        for x0, y0, x1, y1 in np.asarray(buildings, dtype=float).tolist():
            tx1 = (x0 - sx) / dx
            tx2 = (x1 - sx) / dx
            ty1 = (y0 - sy) / dy
            ty2 = (y1 - sy) / dy
            tn = ops.maximum(ops.maximum(ops.minimum(tx1, tx2), ops.minimum(ty1, ty2)), 0.0)
            tf = ops.minimum(ops.minimum(ops.maximum(tx1, tx2), ops.maximum(ty1, ty2)), 1.0)
            hit = (tf - tn) > 1e-9
            blocked = hit if blocked is None else (blocked | hit)
        res[a:a + block] = ~ops.out(blocked)
    return res
