# -*- coding: utf-8 -*-
"""Radio map and per-run radio samples.

:class:`RadioMap` holds everything that is tied to place and does not change
during a run.  For every map pixel in a street and every site it stores

* the line-of-sight state: the building geometry (a link is blocked if the
  straight line crosses a building block) and, with ``clutter`` on, the
  spatially consistent LOS state of 3GPP TR 38.901 (clause 7.6.3.3: a random
  field with 50 m correlation distance compared with the UMi LOS probability),
  which stands for obstacles inside the street such as trees, vehicles and
  street furniture.  The state is a property of the place, the same for every
  user who passes there;
* the path loss for that state and a static, spatially correlated shadowing
  field shared by all users.

It also holds the operator's nominal best-server map (nearest site, no
buildings, no shadowing), the only map handed to the handover rules.

:class:`RadioSource` turns trajectories into received powers, chunk by chunk:
map lookup, plus a time-varying component (moving blockers, updated once per
measurement period), plus, if ``place_share`` < 1, a shadowing process along
each user's own path.  It also draws the noisy L1 samples that feed the UE
measurement filter.  All random numbers of a run come from here and from the
trajectory generator, so every handover rule sees exactly the same radio
conditions for a given seed.

Antenna abstraction (stated once): each site forms a beam of gain ``g_bs_db``
towards the user it serves and towards a user that measures its reference
signals (best SSB beam).  A site serving other users interferes with the mean
gain of its data beams, ``chi`` times the peak gain, scaled by its load.  No
beam management, beam failure or panel orientation is simulated, and there is
no fast fading (assumed averaged out by the wide carrier and the L1 filter).
"""
import time

import numpy as np
from scipy.ndimage import gaussian_filter
from scipy.signal import lfilter
from scipy.spatial import cKDTree
from scipy.special import ndtri

from .backend import NumpyOps
from .layout import los_matrix
from .pathloss import path_loss, p_los_umi, p_los_uma

LN10_10 = np.log(10.0) / 10.0
FLOOR_DB = -300.0


def _streams(seed, n):
    """Independent random generators derived from one seed."""
    return [np.random.default_rng(s) for s in np.random.SeedSequence(int(seed)).spawn(n)]


class _CoarseField:
    """Unit-variance Gaussian random fields (one per site) on a coarse raster.

    Correlation exp(-(d / d_corr)^2); the fields of different sites share a
    common part so that their correlation is ``xcorr``.
    """

    def __init__(self, rng, layout, M, d_corr, res, xcorr):
        self.res = res
        self.x0, self.y0 = layout.xmin - 2 * res, layout.ymin - 2 * res
        self.nx = int((layout.xmax - layout.xmin) / res) + 6
        self.ny = int((layout.ymax - layout.ymin) / res) + 6
        s_pix = (d_corr / 2.0) / res
        ca, cb = np.sqrt(xcorr), np.sqrt(1.0 - xcorr)

        def one():
            g = gaussian_filter(rng.standard_normal((self.ny, self.nx), dtype=np.float32), s_pix, mode="wrap")
            return g / g.std()
        common = one() if xcorr > 0 else 0.0
        self.f = np.empty((self.ny, self.nx, M), dtype=np.float32)
        for m in range(M):
            self.f[:, :, m] = ca * common + cb * one()

    def at(self, x, y):
        """Bilinear interpolation at points (P,) -> (P, M)."""
        gx = np.clip((x - self.x0) / self.res, 0.0, self.nx - 1.001)
        gy = np.clip((y - self.y0) / self.res, 0.0, self.ny - 1.001)
        ix, iy = gx.astype(int), gy.astype(int)
        tx, ty = (gx - ix).astype(np.float32)[:, None], (gy - iy).astype(np.float32)[:, None]
        f = self.f
        return (f[iy, ix] * (1 - tx) * (1 - ty) + f[iy, ix + 1] * tx * (1 - ty)
                + f[iy + 1, ix] * (1 - tx) * ty + f[iy + 1, ix + 1] * tx * ty)


class RadioMap:
    """Static radio map of one environment realisation."""

    def __init__(self, layout, radio, seed, ops=None, clutter=True):
        self.layout, self.radio, self.ops = layout, radio, ops or NumpyOps()
        ops = self.ops
        self.is_grid = layout.env == "grid"
        res = float(radio.map_res) if self.is_grid else max(float(radio.map_res), 2.0)
        pad = 3.0 * res
        self.res = res
        self.x0, self.y0 = layout.xmin - pad, layout.ymin - pad
        self.nx = int(np.ceil((layout.xmax - layout.xmin + 2 * pad) / res)) + 1
        self.ny = int(np.ceil((layout.ymax - layout.ymin + 2 * pad) / res)) + 1
        M = layout.M
        gx = self.x0 + np.arange(self.nx) * res
        gy = self.y0 + np.arange(self.ny) * res
        XX, YY = np.meshgrid(gx, gy)
        rng_f, rng_c = _streams(seed * 1000003 + 11, 2)

        # nominal plan on a 2 m raster: nearest site (equal power and height: nearest = strongest without buildings)
        self.nres = 2.0
        nnx = int((layout.xmax - layout.xmin + 2 * pad) / self.nres) + 2
        nny = int((layout.ymax - layout.ymin + 2 * pad) / self.nres) + 2
        NX, NY = np.meshgrid(self.x0 + np.arange(nnx) * self.nres, self.y0 + np.arange(nny) * self.nres)
        self.best_nom = cKDTree(layout.sites).query(np.c_[NX.ravel(), NY.ravel()])[1].reshape(nny, nnx).astype(np.int16)

        mask = layout.street_mask(XX, YY, margin=2.0 * res)
        px, py = XX[mask], YY[mask]
        P = len(px)
        self.n_pix = P
        self.idx = np.full((self.ny, self.nx), P, dtype=np.int64)       # pixel -> row; off-street pixels -> dummy row P
        self.idx[mask] = np.arange(P)
        self.has_field = radio.place_share > 0.0
        field = None
        if self.has_field:
            fres = min(2.0, radio.d_corr / 4.0) if radio.d_corr >= 4.0 else res
            field = _CoarseField(rng_f, layout, M, radio.d_corr, max(fres, res), radio.xcorr).at(px, py)
            field *= np.float32(np.sqrt(radio.place_share))
        self.los = None
        if self.is_grid:
            los = los_matrix(px, py, layout.sites, layout.buildings, ops)
            d2 = np.hypot(px[:, None] - layout.sites[None, :, 0], py[:, None] - layout.sites[None, :, 1])
            if clutter:
                lat = _CoarseField(rng_c, layout, M, radio.los_corr, 5.0, 0.0).at(px, py)
                p = p_los_umi(d2) if radio.pl_model == "umi" else p_los_uma(d2)
                los &= lat < ndtri(np.clip(p, 1e-9, 1.0 - 1e-9))
            pl = ops.out(path_loss(ops.arr(d2), ops.arr(los, "?"), radio, ops))
            gain = -pl.astype(np.float32)
            if field is not None:
                gain += field * np.where(los, np.float32(radio.sf_los), np.float32(radio.sf_nlos))
            self.los = np.vstack([los, np.zeros((1, M), dtype=bool)])
            self.los_share = float(los.mean())
        else:
            gain = field if field is not None else np.zeros((P, M), dtype=np.float32)
        fill = FLOOR_DB if self.is_grid else 0.0
        self.gain = np.vstack([gain, np.full((1, M), fill, dtype=np.float32)])   # (P + 1, M)
        self._gain_dev = None

    # ------------------------------------------------------------------
    def _index(self, x, y):
        gx = np.clip((np.asarray(x, dtype=float) - self.x0) / self.res, 0.0, self.nx - 1.001)
        gy = np.clip((np.asarray(y, dtype=float) - self.y0) / self.res, 0.0, self.ny - 1.001)
        return gx, gy

    def lookup(self, x, y):
        """Bilinear interpolation of the static map at points (P,) -> (P, M) float32."""
        ops = self.ops
        if self._gain_dev is None:
            self._gain_dev = ops.arr(self.gain, "f4")
        g = self._gain_dev
        gx, gy = self._index(x, y)
        ix, iy = gx.astype(np.int64), gy.astype(np.int64)
        tx = (gx - ix).astype(np.float32)
        ty = (gy - iy).astype(np.float32)
        idx = self.idx
        w = ops.arr(np.stack([(1 - tx) * (1 - ty), tx * (1 - ty), (1 - tx) * ty, tx * ty]), "f4")
        p = ops.arr(np.stack([idx[iy, ix], idx[iy, ix + 1], idx[iy + 1, ix], idx[iy + 1, ix + 1]]), "i8")
        v = ops.take(g, p[0]) * w[0][:, None]
        for q in (1, 2, 3):
            v += ops.take(g, p[q]) * w[q][:, None]
        return ops.out(v)

    def los_at(self, x, y):
        """Line-of-sight state at points (nearest pixel) -> (P, M) bool (grid only)."""
        gx, gy = self._index(x, y)
        return self.los[self.idx[np.rint(gy).astype(int), np.rint(gx).astype(int)]]

    def nominal_cell(self, x, y):
        """Nominal best server (nearest site) at points of any shape."""
        ny, nx = self.best_nom.shape
        ix = np.clip(np.rint((np.asarray(x) - self.x0) / self.nres).astype(int), 0, nx - 1)
        iy = np.clip(np.rint((np.asarray(y) - self.y0) / self.nres).astype(int), 0, ny - 1)
        return self.best_nom[iy, ix]


class Chunk:
    """Radio samples of consecutive steps ``k0 .. k0+n-1``.

    ``rsrp`` (n, U, M) received power [dBm], ``lin`` the same in mW, ``l1`` the
    noisy L1 samples at the measurement instants (steps with k % mp == 0).
    """
    __slots__ = ("k0", "n", "rsrp", "lin", "l1", "mp")

    def __init__(self, k0, n, rsrp, lin, l1, mp):
        self.k0, self.n, self.rsrp, self.lin, self.l1, self.mp = k0, n, rsrp, lin, l1, mp


class RadioSource:
    """Received power of every site at every user and step, produced in chunks."""

    def __init__(self, rmap, traj, sc, chunk=1000):
        self.rmap, self.sc, self.traj = rmap, sc, traj
        self.X, self.Y, self.V, self.TH = traj
        self.S, self.U = self.X.shape
        self.M = rmap.layout.M
        R = sc.radio
        dt = sc.proto.dt
        self.mp = max(1, int(round(sc.proto.meas_period / dt)))
        self.chunk = max(self.mp, (chunk // self.mp) * self.mp)      # whole measurement periods per chunk
        self.rng_t, self.rng_o, self.rng_m, self.rng_l = _streams(sc.seed * 1000003 + 29, 4)
        self.r_t = float(np.exp(-self.mp * dt / R.tau_t))            # per measurement period
        self.zt = self.rng_t.standard_normal((self.U, self.M))       # stationary start
        self.own = R.place_share < 1.0
        self.r_o = np.exp(-self.V * dt / R.d_corr)                   # per user and step
        self.zo = self.rng_o.standard_normal((self.U, self.M)) if self.own else None
        self.open = not rmap.is_grid
        if self.open:
            self.r_l = np.exp(-self.V * dt / R.los_corr)
            self.zl = self.rng_l.standard_normal((self.U, self.M))
        self.p0 = R.tx_dbm + R.g_bs_db + R.g_ue_db
        self.t_lookup = 0.0

    @staticmethod
    def _ar1(w, r, z):
        """Unit-variance AR(1) along axis 0 with coefficient ``r`` and previous value ``z``."""
        y, _ = lfilter([np.sqrt(1.0 - r * r)], [1.0, -r], w, axis=0, zi=(r * z)[None])
        return y

    def _ar1_users(self, rng, r_u, z, n):
        """AR(1) along time with one coefficient per user -> (n, U, M)."""
        out = np.empty((n, self.U, self.M))
        for u in range(self.U):
            out[:, u, :] = self._ar1(rng.standard_normal((n, self.M)), r_u[u], z[u])
        return out

    def chunks(self):
        """Yield :class:`Chunk` objects covering the whole run in order."""
        R = self.sc.radio
        rmap = self.rmap
        sites = rmap.layout.sites
        for k0 in range(0, self.S, self.chunk):
            k1 = min(self.S, k0 + self.chunk)
            n = k1 - k0
            x = self.X[k0:k1].ravel()
            y = self.Y[k0:k1].ravel()
            shape = (n, self.U, self.M)
            sig = None
            if rmap.is_grid:
                ta = time.perf_counter()
                rs = rmap.lookup(x, y).astype(np.float64).reshape(shape)
                self.t_lookup += time.perf_counter() - ta
                if self.own:
                    sig = np.where(rmap.los_at(x, y), R.sf_los, R.sf_nlos).reshape(shape)
            else:
                d2 = np.hypot(x[:, None] - sites[None, :, 0], y[:, None] - sites[None, :, 1])
                p = p_los_umi(d2) if R.pl_model == "umi" else p_los_uma(d2)
                g = self._ar1_users(self.rng_l, self.r_l, self.zl, n)
                self.zl = g[-1].copy()
                los = g.reshape(d2.shape) < ndtri(np.clip(p, 1e-9, 1.0 - 1e-9))
                rs = -path_loss(d2, los, R).reshape(shape)
                sig = np.where(los, R.sf_los, R.sf_nlos).reshape(shape)
                if rmap.has_field:
                    rs += rmap.lookup(x, y).astype(np.float64).reshape(shape) * sig
            if self.own:
                o = self._ar1_users(self.rng_o, self.r_o, self.zo, n)
                self.zo = o[-1].copy()
                rs += np.sqrt(1.0 - R.place_share) * sig * o
            nm = -(-n // self.mp)
            if R.sigma_t > 0:
                zt = self._ar1(self.rng_t.standard_normal((nm, self.U, self.M)), self.r_t, self.zt)
                self.zt = zt[-1].copy()
                rs += R.sigma_t * np.repeat(zt, self.mp, axis=0)[:n]
            rs += self.p0
            l1 = rs[::self.mp] + R.meas_sigma * self.rng_m.standard_normal((nm, self.U, self.M))
            yield Chunk(k0, n, rs, np.exp(rs * LN10_10), l1, self.mp)
