# -*- coding: utf-8 -*-
"""Handover rules.

Two families exist, distinguished by ``kind``:

``"bho"`` (baseline handover): the UE reports when Event A3 holds for the
time-to-trigger, the network prepares the target and sends a handover command.
  * :class:`A3`              fixed offset and time-to-trigger.
  * :class:`PerUserMargin`   the per-user, per-neighbour margin of the group's
    earlier work: outcome history of the cell pair and path overlap move the
    A3 offset of every neighbour.

``"cho"`` (conditional handover, 3GPP Rel-16): the UE reports neighbours that
pass a preparation offset, the network prepares up to ``n_max`` of them and
gives each a conditional configuration with an execution offset; the UE
executes on its own when the execution condition holds.
  * :class:`Cho`             fixed preparation and execution offsets.
  * :class:`MemCho`          the scheme under study: a place-keyed memory of
    handover outcomes and the predicted path of the UE shift the preparation
    offset and the execution offset per user and neighbour.  With all weights
    zero it is exactly :class:`Cho`.

A rule only sees what a network can see: filtered measurement reports, the
reported position and velocity of the UE, the nominal site plan, and the
outcome of past handovers as the engine reports it (dwell time, measured gain,
failure type).  It never sees the true SINR, the buildings or the load.
"""
import numpy as np

from .services import SVC_W

L_USEFUL, L_UNNEC, L_EARLY, L_LATE = 0, 1, 2, 3     # labels fed back to a rule

# quadrature of the predicted-motion sector: 6 radii (equal-area rings) x 8 angles
_RR = np.sqrt((np.arange(6) + 0.5) / 6.0)
_AA = (np.arange(8) + 0.5) / 8.0 * 2 - 1
_QR, _QA = (g.ravel() for g in np.meshgrid(_RR, _AA))


def path_overlap(rmap, x, y, v, th, t_p=3.0, half_angle=0.6, r_min=10.0):
    """Share of the predicted-motion sector that lies in each cell's nominal area.

    The sector has radius ``v * t_p`` (at least ``r_min``) and opening
    +-``half_angle`` around the heading; the nominal area of a cell is where it
    is the nearest site.  Deterministic 48-point quadrature.  Returns (U, M).
    """
    R = np.maximum(v * t_p, r_min)[:, None] * _QR[None, :]
    ang = th[:, None] + half_angle * _QA[None, :]
    best = rmap.nominal_cell(x[:, None] + R * np.cos(ang), y[:, None] + R * np.sin(ang))
    U, M = len(x), rmap.layout.M
    out = np.bincount((np.arange(U)[:, None] * M + best).ravel(), minlength=U * M)
    return out.reshape(U, M) / float(best.shape[1])


class Rule:
    """Common part of all rules."""
    kind = "bho"
    name = "rule"
    late_leads = (0.0,)        # look-back times [s] at which a late failure is written to the memory
    learns = False             # True if the rule uses the outcome feedback

    def reset(self, eng):
        """Called once before a run; ``eng`` is the engine (gives U, M, radio map, scenario)."""
        self.U, self.M, self.rmap, self.sc = eng.U, eng.M, eng.rmap, eng.sc
        self.svc = eng.svc

    def keys(self, ctx):
        """Memory key of every user at the current instant (or None)."""
        return None

    def key_at(self, x, y, th):
        return -1

    def on_outcome(self, u, src, tgt, key, label, t):
        """Outcome of a handover attempt of user ``u`` (label L_USEFUL .. L_LATE)."""

    def on_late(self, u, src, cell, keys, t):
        """Radio-link failure without a handover; the UE re-established in ``cell``."""

    def describe(self):
        return dict(name=self.name, kind=self.kind, **getattr(self, "par", {}))


# ----------------------------------------------------------------------------
# baseline handover
# ----------------------------------------------------------------------------
class A3(Rule):
    """Event A3 with one offset [dB] and one time-to-trigger [s] for all users."""
    kind = "bho"

    def __init__(self, off=3.0, ttt=0.16, name="A3"):
        self.off, self.ttt, self.name = float(off), float(ttt), name
        self.par = dict(off=off, ttt=ttt)

    def offsets(self, ctx):
        return self.off


class PairTable:
    """Outcome counts per (source, target) with exponential forgetting."""

    def __init__(self, M, tau=600.0):
        self.N = np.zeros((M, M, 4))
        self.tau, self.t_last = tau, 0.0

    def _decay(self, t):
        if self.tau and t - self.t_last >= 10.0:
            self.N *= np.exp(-(t - self.t_last) / self.tau)
            self.t_last = t

    def add(self, src, tgt, label, t):
        self._decay(t)
        self.N[src, tgt, label] += 1.0


class PerUserMargin(Rule):
    """A3 whose offset is set per user and neighbour (the earlier 5G rule).

    offset(u, n) = clip(h0 + eta_h * H(s, n) - eta_l * L(s, n) + eta_s * w(service)
                        - eta_a * overlap(u, n), 0, cap)

    H is the smoothed share of unnecessary and failed handovers s -> n, L the
    share of late ones, overlap the path-overlap term.  With all ``eta`` zero the
    rule is A3 with offset ``h0``.
    """
    kind = "bho"
    learns = True

    def __init__(self, h0=2.0, ttt=0.16, eta_h=8.0, eta_l=0.0, eta_a=4.0, eta_s=0.0, cap=9.0,
                 alpha=0.6, beta=1.0, tau=600.0, t_p=3.0, name="PUM"):
        self.h0, self.ttt, self.eta_h, self.eta_l, self.eta_a, self.eta_s = h0, float(ttt), eta_h, eta_l, eta_a, eta_s
        self.cap, self.alpha, self.beta, self.tau, self.t_p, self.name = cap, alpha, beta, tau, t_p, name
        self.par = dict(h0=h0, ttt=ttt, eta_h=eta_h, eta_l=eta_l, eta_a=eta_a, eta_s=eta_s, cap=cap)
        self.plain = not (eta_h or eta_l or eta_a or eta_s)

    def reset(self, eng):
        super().reset(eng)
        self.tab = PairTable(self.M, self.tau)
        self.refresh = max(eng.sc.proto.report_interval, eng.sc.proto.meas_period)
        self._t_off, self._off = -1e9, None

    def offsets(self, ctx):
        if self.plain:
            return float(self.h0)
        if ctx["t"] - self._t_off < self.refresh - 1e-9:      # offsets are rewritten once per report interval
            return self._off
        self._t_off = ctx["t"]
        self._off = self._offsets(ctx)
        return self._off

    def _offsets(self, ctx):
        serv = ctx["serv"]
        N = self.tab.N[serv]                                    # (U, M, 4)
        tot = N.sum(2) + 4 * self.beta
        off = np.full((self.U, self.M), float(self.h0))
        if self.eta_h:
            off += self.eta_h * (self.alpha * (N[..., 1] + self.beta) + (1 - self.alpha) * (N[..., 2] + self.beta)) / tot
        if self.eta_l:
            off -= self.eta_l * (N[..., 3] + self.beta) / tot
        if self.eta_s:
            off += (self.eta_s * SVC_W[self.svc])[:, None]
        if self.eta_a:
            off -= self.eta_a * path_overlap(self.rmap, ctx["x"], ctx["y"], ctx["v"], ctx["th"], self.t_p)
        return np.clip(off, 0.0, self.cap)

    def on_outcome(self, u, src, tgt, key, label, t):
        self.tab.add(src, tgt, label, t)

    def on_late(self, u, src, cell, keys, t):
        self.tab.add(src, cell, L_LATE, t)


# ----------------------------------------------------------------------------
# conditional handover
# ----------------------------------------------------------------------------
class Cho(Rule):
    """Conditional handover with fixed offsets.

    o_prep    preparation offset [dB]: a neighbour is reported and prepared when
              it is stronger than the serving cell plus this offset for ``ttt_prep``
    o_exec    execution offset [dB] written into the conditional configuration
    ttt_exec  time-to-trigger of the execution condition [s]
    n_max     size limit of the prepared set (the standard allows up to 8)
    rel_hys   a prepared cell is released when it falls ``rel_hys`` dB below its
              preparation offset
    immediate the UE executes as soon as the configuration arrives (the
              conditional handover then acts as a baseline handover; checks only)
    """
    kind = "cho"
    stick = 1.0                 # ranking bonus of an already prepared cell [dB] (avoids churn at a full set)

    def __init__(self, o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, ttt_prep=0.0, n_max=4, rel_hys=3.0,
                 immediate=False, name="CHO"):
        self.o_prep, self.o_exec, self.ttt_exec, self.ttt_prep = float(o_prep), float(o_exec), float(ttt_exec), float(ttt_prep)
        self.n_max, self.rel_hys, self.immediate, self.name = int(n_max), float(rel_hys), immediate, name
        self.o_rep = self.o_prep
        if immediate:
            self.stick = np.inf     # the cell chosen at the report is never replaced
        self.par = dict(o_prep=o_prep, o_exec=o_exec, ttt_exec=ttt_exec, ttt_prep=ttt_prep, n_max=n_max, rel_hys=rel_hys)

    def prep_offsets(self, ctx):
        return self.o_prep

    def exec_offsets(self, ctx):
        return -np.inf if self.immediate else self.o_exec


class PlaceTable:
    """Outcome counts per (place bin, target cell) with exponential forgetting.

    A place bin is a square of ``res`` metres combined with the heading
    quadrant, so the two directions of a street are kept apart.
    """

    def __init__(self, layout, M, res=10.0, tau=600.0):
        self.res = res
        self.x0, self.y0 = layout.xmin - res, layout.ymin - res
        self.nx = int((layout.xmax - layout.xmin) / res) + 3
        self.ny = int((layout.ymax - layout.ymin) / res) + 3
        self.N = np.zeros((self.nx * self.ny * 4, M, 4), dtype=np.float32)
        self.tau, self.t_last = tau, 0.0

    def bins(self, x, y, th):
        ix = np.clip(((np.asarray(x) - self.x0) / self.res).astype(int), 0, self.nx - 1)
        iy = np.clip(((np.asarray(y) - self.y0) / self.res).astype(int), 0, self.ny - 1)
        q = np.rint(np.asarray(th) / (np.pi / 2)).astype(int) % 4
        return (iy * self.nx + ix) * 4 + q

    def add(self, b, tgt, label, t):
        if self.tau and t - self.t_last >= 10.0:
            self.N *= np.float32(np.exp(-(t - self.t_last) / self.tau))
            self.t_last = t
        self.N[b, tgt, label] += 1.0


class MemCho(Cho):
    """Conditional handover steered by outcome memory and motion (the scheme under study).

    For user u in place bin b (position and heading quadrant) and neighbour n:

        bad(u, n)   estimated share of handovers to n decided here that ended
                    unnecessary, too early or in the wrong cell
        late(u, n)  estimated share of events here that were late failures after
                    which the UE re-established in n
        ovl(u, n)   path overlap of the predicted motion with the area of n

        O_exec(u, n) = clip(o_exec + w_u (bad - bad_mean) - w_l late - w_a ovl, O_LO, O_HI)
        O_prep(u, n) = max(o_prep + v_u (bad - bad_mean) - v_l late - v_a ovl, O_rep)

    A neighbour is prepared when its measured advantage reaches O_prep(u, n) and
    it is among the ``n_max`` best by that margin; O_exec(u, n) is fixed when the
    cell is prepared and travels in the conditional configuration (the standard
    carries one execution offset per candidate).  The UE reports from the lower
    offset O_rep = o_prep - min(v_u + v_l + v_a, REP_CAP); with zero weights this
    equals o_prep and the rule is :class:`Cho`.

    Estimates are shrunk towards the cell-pair level with ``kappa`` pseudo-counts
    (``place=False`` uses the cell-pair level only).  ``pos_err`` / ``head_err``
    add errors to the reported position [m] and heading [rad].
    """
    learns = True
    O_LO, O_HI = -1.0, 12.0
    REP_CAP = 6.0
    late_leads = (0.0, 0.5, 1.0)

    def __init__(self, o_prep=-2.0, o_exec=3.0, ttt_exec=0.08, ttt_prep=0.0, n_max=4, rel_hys=3.0,
                 w_u=0.0, w_l=0.0, w_a=0.0, v_u=0.0, v_l=0.0, v_a=0.0,
                 kappa=3.0, kappa0=3.0, res=10.0, tau=600.0, t_p=3.0, place=True,
                 pos_err=0.0, head_err=0.0, name="MemCHO"):
        super().__init__(o_prep, o_exec, ttt_exec, ttt_prep, n_max, rel_hys, False, name)
        self.w_u, self.w_l, self.w_a, self.v_u, self.v_l, self.v_a = w_u, w_l, w_a, v_u, v_l, v_a
        self.kappa, self.kappa0, self.res, self.tau, self.t_p, self.place = kappa, kappa0, res, tau, t_p, place
        self.pos_err, self.head_err = pos_err, head_err
        self.o_rep = self.o_prep - min(v_u + v_l + v_a, self.REP_CAP)
        self.use_mem = bool(w_u or w_l or v_u or v_l)
        self.use_mot = bool(w_a or v_a)
        self.par.update(w_u=w_u, w_l=w_l, w_a=w_a, v_u=v_u, v_l=v_l, v_a=v_a, kappa=kappa, res=res, place=place)
        self._stamp = None

    def reset(self, eng):
        super().reset(eng)
        self.ptab = PlaceTable(self.rmap.layout, self.M, self.res, self.tau)
        self.pair = PairTable(self.M, self.tau)
        self.glob = np.zeros(4)
        self.rng = np.random.default_rng(self.sc.seed * 1000003 + 71)
        self._stamp = None

    # reported position / heading (with the optional errors)
    def _where(self, ctx):
        x, y, th = ctx["x"], ctx["y"], ctx["th"]
        if self.pos_err:
            e = self.rng.normal(0.0, self.pos_err, (2, self.U))
            x, y = x + e[0], y + e[1]
        if self.head_err:
            th = th + self.rng.normal(0.0, self.head_err, self.U)
        return x, y, th

    def _features(self, ctx):
        """bad - mean, late, overlap, key; cached for the instant."""
        if self._stamp == ctx["k"]:
            return self._feat
        x, y, th = self._where(ctx)
        key = self.ptab.bins(x, y, th)
        dbad = late = ovl = 0.0
        if self.use_mem:
            g = self.glob
            mean_bad = (g[1] + g[2] + 1.0) / (g[0] + g[1] + g[2] + 2.0)
            C = self.pair.N[ctx["serv"]]
            ok = C[..., 0] + C[..., 1] + C[..., 2]
            bad = (C[..., 1] + C[..., 2] + self.kappa0 * mean_bad) / (ok + self.kappa0)
            late = C[..., 3] / (ok + C[..., 3] + self.kappa0)
            if self.place:
                c = self.ptab.N[key]
                okp = c[..., 0] + c[..., 1] + c[..., 2]
                bad = (c[..., 1] + c[..., 2] + self.kappa * bad) / (okp + self.kappa)
                late = (c[..., 3] + self.kappa * late) / (okp + c[..., 3] + self.kappa)
            dbad = bad - mean_bad
        if self.use_mot:
            ovl = path_overlap(self.rmap, x, y, ctx["v"], th, self.t_p)
        self._feat = (dbad, late, ovl, key)
        self._stamp = ctx["k"]
        return self._feat

    def keys(self, ctx):
        return self._features(ctx)[3]

    def key_at(self, x, y, th):
        return int(self.ptab.bins(x, y, th))

    def prep_offsets(self, ctx):
        if not (self.v_u or self.v_l or self.v_a):
            return self.o_prep
        dbad, late, ovl, _ = self._features(ctx)
        return np.maximum(self.o_prep + self.v_u * dbad - self.v_l * late - self.v_a * ovl, self.o_rep)

    def exec_offsets(self, ctx):
        if not (self.w_u or self.w_l or self.w_a):
            return self.o_exec
        dbad, late, ovl, _ = self._features(ctx)
        return np.clip(self.o_exec + self.w_u * dbad - self.w_l * late - self.w_a * ovl, self.O_LO, self.O_HI)

    def on_outcome(self, u, src, tgt, key, label, t):
        if key is not None and key >= 0:
            self.ptab.add(key, tgt, label, t)
        self.pair.add(src, tgt, label, t)
        self.glob[label] += 1.0

    def on_late(self, u, src, cell, keys, t):
        for b in keys:
            if b >= 0:
                self.ptab.add(b, cell, L_LATE, t)
        self.pair.add(src, cell, L_LATE, t)
        self.glob[L_LATE] += 1.0


RULES = {"a3": A3, "pum": PerUserMargin, "cho": Cho, "memcho": MemCho}


def make_rule(spec):
    """Build a rule from ``{"rule": "a3" | "pum" | "cho" | "memcho", "name": ..., <parameters>}``."""
    d = dict(spec)
    cls = RULES[d.pop("rule")]
    return cls(**d)
