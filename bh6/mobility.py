# -*- coding: utf-8 -*-
"""Mobility profiles and trajectories.

Street grid: users follow the street centre lines and turn at intersections
(straight 0.5, left 0.25, right 0.25, as in the urban case of 3GPP TR 36.885 /
37.885); each user keeps a constant lateral displacement and a constant speed.
Open area: straight legs between random waypoints.
"""
import numpy as np

# name -> list of (share, v_min, v_max [m/s], lateral displacement range [m])
PROFILES = {
    "ped": [(1.0, 1.2, 1.8, (6.5, 8.5))],          # pedestrians on the pavement
    "veh8": [(1.0, 7.2, 8.8, (0.0, 3.0))],         # slow urban traffic, about 30 km/h
    "veh16": [(1.0, 14.4, 17.6, (0.0, 3.0))],      # about 60 km/h
    "veh30": [(1.0, 27.0, 33.0, (0.0, 3.0))],      # stress case, about 110 km/h
    "mix": [(0.4, 1.2, 1.8, (6.5, 8.5)), (0.3, 7.2, 8.8, (0.0, 3.0)), (0.3, 14.4, 17.6, (0.0, 3.0))],
    # constant speeds on the centre line, used for the comparison with the ns-3 study
    "c8": [(1.0, 8.0, 8.0, (0.0, 0.0))],
    "c16": [(1.0, 16.0, 16.0, (0.0, 0.0))],
    "c30": [(1.0, 30.0, 30.0, (0.0, 0.0))],
}

_DX = np.array([1.0, 0.0, -1.0, 0.0])      # heading index 0: east, 1: north, 2: west, 3: south
_DY = np.array([0.0, 1.0, 0.0, -1.0])


def _draw_users(profile, U, rng):
    """Speed and lateral displacement of every user."""
    parts = PROFILES[profile]
    cls = rng.choice(len(parts), size=U, p=np.array([p[0] for p in parts]) / sum(p[0] for p in parts))
    v = np.empty(U)
    off = np.empty((U, 2))
    for u in range(U):
        _, v0, v1, (o0, o1) = parts[cls[u]]
        v[u] = rng.uniform(v0, v1)
        off[u] = rng.uniform(o0, o1, 2) * rng.choice([-1.0, 1.0], 2)
    return v, off


def _grid_waypoints(layout, v, t_end, rng):
    """Break points (t, x, y, heading index) of one user on the street grid."""
    xs, ys = layout.xs, layout.ys
    len_ew = (xs[-1] - xs[0]) * len(ys)
    len_ns = (ys[-1] - ys[0]) * len(xs)
    if rng.random() < len_ew / (len_ew + len_ns):
        y = ys[rng.integers(len(ys))]
        x = rng.uniform(xs[0], xs[-1])
        h = int(rng.choice([0, 2]))
    else:
        x = xs[rng.integers(len(xs))]
        y = rng.uniform(ys[0], ys[-1])
        h = int(rng.choice([1, 3]))
    T, Xb, Yb, Hb = [0.0], [x], [y], [h]
    t = 0.0
    while t < t_end:
        # next intersection ahead
        if h == 0:
            nx_, ny_ = xs[xs > x + 1e-6].min(), y
        elif h == 2:
            nx_, ny_ = xs[xs < x - 1e-6].max(), y
        elif h == 1:
            nx_, ny_ = x, ys[ys > y + 1e-6].min()
        else:
            nx_, ny_ = x, ys[ys < y - 1e-6].max()
        t += (abs(nx_ - x) + abs(ny_ - y)) / v
        x, y = nx_, ny_
        # choose the next heading among the streets that continue inside the area
        ok = []
        for turn, w in ((0, 0.5), (1, 0.25), (3, 0.25)):
            hh = (h + turn) % 4
            ex, ey = x + _DX[hh], y + _DY[hh]
            if xs[0] - 1e-6 <= ex <= xs[-1] + 1e-6 and ys[0] - 1e-6 <= ey <= ys[-1] + 1e-6:
                ok.append((hh, w))
        if ok:
            ws = np.array([w for _, w in ok])
            h = ok[int(rng.choice(len(ok), p=ws / ws.sum()))][0]
        else:
            h = (h + 2) % 4
        T.append(t); Xb.append(x); Yb.append(y); Hb.append(h)
    return np.array(T), np.array(Xb), np.array(Yb), np.array(Hb)


def _open_waypoints(layout, v, t_end, rng, margin=10.0):
    """Break points of one user in the open area (random waypoints, straight legs)."""
    x0, x1, y0, y1 = layout.xmin + margin, layout.xmax - margin, layout.ymin + margin, layout.ymax - margin
    x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
    T, Xb, Yb = [0.0], [x], [y]
    t = 0.0
    while t < t_end:
        nx_, ny_ = rng.uniform(x0, x1), rng.uniform(y0, y1)
        t += max(np.hypot(nx_ - x, ny_ - y), 1.0) / v
        x, y = nx_, ny_
        T.append(t); Xb.append(x); Yb.append(y)
    return np.array(T), np.array(Xb), np.array(Yb), None


def gen_traj(layout, sc, rng):
    """Trajectories of all users.

    Returns ``X, Y`` (S, U) positions [m], ``V`` (U,) speeds [m/s] and ``TH``
    (S, U) headings [rad], one row per simulation step.
    """
    dt = sc.proto.dt
    S = int(round(sc.t_sim / dt))
    U = sc.n_ue
    v, off = _draw_users(sc.profile, U, rng)
    if layout.env != "grid":
        off[:] = 0.0
    t = np.arange(S) * dt
    X = np.empty((S, U)); Y = np.empty((S, U)); TH = np.empty((S, U), dtype=np.float32)
    for u in range(U):
        if layout.env == "grid":
            T, Xb, Yb, Hb = _grid_waypoints(layout, v[u], sc.t_sim + dt, rng)
        else:
            T, Xb, Yb, Hb = _open_waypoints(layout, v[u], sc.t_sim + dt, rng)
        X[:, u] = np.interp(t, T, Xb) + off[u, 0]
        Y[:, u] = np.interp(t, T, Yb) + off[u, 1]
        leg = np.clip(np.searchsorted(T, t, side="right") - 1, 0, len(T) - 2)
        if Hb is not None:
            TH[:, u] = np.arctan2(_DY[Hb[leg]], _DX[Hb[leg]])
        else:
            TH[:, u] = np.arctan2(Yb[leg + 1] - Yb[leg], Xb[leg + 1] - Xb[leg])
    return X, Y, v, TH
