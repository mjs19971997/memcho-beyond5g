# -*- coding: utf-8 -*-
"""Protocol engine: measurements, handover procedures, failures, outcome labels.

One :class:`Engine` simulates one handover rule on given radio samples.  All
users advance together on a 10 ms grid; cell load and interference are coupled
through the users' serving cells.  The engine itself draws no random numbers,
so two rules run on the same radio samples differ only through their decisions.

Chain of a baseline handover (rule kind "bho")
    L1 sample every ``meas_period`` -> L3 filter -> Event A3 (offset per user and
    neighbour) held for the time-to-trigger -> measurement report -> preparation
    (``t_prep``) -> handover command.  The command is lost if T310 is running
    when it arrives (handover failure of TR 36.839, "too late").  Otherwise the
    UE leaves the source, is interrupted for ``t_exec`` and joins the target if
    the target SINR is at least Qout; if not, the execution fails.

Chain of a conditional handover (rule kind "cho")
    The UE reports a neighbour when it passes the reporting offset (first report
    at once, then every ``report_interval``).  At a report the network prepares
    the neighbours whose advantage reaches the preparation offset, at most
    ``n_max`` (best margin first), and releases prepared cells that fell
    ``rel_hys`` below it.  The conditional configuration reaches the UE after
    ``t_prep`` and is lost if T310 is running.  The UE checks the execution
    condition of every prepared cell at each measurement and executes on its
    own; no command is needed.  After a successful execution the other prepared
    cells are released (Rel-16 behaviour).  After a failure the UE recovers
    faster (``t_cho_rec``) if the cell it selects is a prepared one.

Radio-link monitoring
    Serving SINR smoothed over the Qout / Qin windows; N310 out-of-sync
    indications start T310, N311 in-sync indications stop it, expiry is a
    radio-link failure followed by re-establishment in the strongest cell.

Outcome of a handover attempt (exactly one per attempt)
    late         command lost, or link failure while the handover was prepared
    early        execution failed, or link failure in the target before the
                 evaluation window closed, and the UE re-established in the
                 source or again in the target
    wrong        the same, but the UE re-established in a third cell
    unnecessary  completed; the source would not have failed during the window
                 and (the stay was shorter than T_min of the service or the mean
                 SINR gain over the window was below theta_Q)
    useful       completed and not unnecessary
    censored     the run ended before the outcome was known
A link failure with no handover in flight and no open window is not an attempt.
It is "too late" (MRO sense) if the UE re-establishes in another cell and a
coverage failure if it re-establishes in the same cell.

The SINR used by the label is computed from the true received powers with all
cells transmitting (``label_load`` = 1) and does not depend on what a rule does
to the load.  What a rule learns from is the observable counterpart (filtered
reports, dwell time, failure type).
"""
import time

import numpy as np

from .services import SVC_TMIN, SVC_THQ, SVC_GBR, SVC_RATE
from .policies import L_USEFUL, L_UNNEC, L_EARLY, L_LATE

EPS = 1e-9
LN10_10 = np.log(10.0) / 10.0
INF = np.inf
ST_CONN, ST_EXEC, ST_REEST = 0, 1, 2
OUTCOMES = ("useful", "unnecessary", "early", "wrong", "late", "censored")
CAUSES = ("late_cmd", "late_prep", "late_rlf", "cov_rlf", "exec_fail", "early_rlf")
EVENT_FIELDS = ("t_attempt", "t_exec", "t_end", "ue", "kind", "src", "tgt", "outcome", "cause",
                "dwell", "gain_db", "n_prepared", "o_exec", "x", "y")


class Engine:
    """Simulation of one rule.  Feed the chunks in order, then call :meth:`finish`."""

    def __init__(self, sc, layout, rmap, traj, svc, bg, rule, log_events=True):
        self.sc, self.layout, self.rmap, self.rule = sc, layout, rmap, rule
        self.X, self.Y, self.V, self.TH = traj
        self.S, self.U = self.X.shape
        self.M = layout.M
        self.svc = svc
        P, R, L = sc.proto, sc.radio, sc.load
        self.P = P
        self.dt = P.dt
        self.mp = max(1, int(round(P.meas_period / P.dt)))
        self.mdt = self.mp * P.dt
        self.rep = max(1, int(round(P.report_interval / self.mdt)))
        self.lab_every = max(1, int(round(P.lab_period / self.mdt)))
        self.learns = bool(getattr(rule, "learns", True))
        a200 = 0.5 ** (P.l3_k / 4.0)                          # TS 38.331: F_n = (1-a) F_{n-1} + a M_n, a = 1/2^(k/4)
        self.a3 = 1.0 - (1.0 - a200) ** (self.mdt / 0.2)      # same time characteristic at another sample rate
        self.ao = 1.0 - np.exp(-P.dt / P.qout_win)
        self.ai = 1.0 - np.exp(-P.dt / P.qin_win)
        self.qout = 10 ** (P.qout_db / 10.0)
        self.qin = 10 ** (P.qin_db / 10.0)
        self.noise = 10 ** (R.noise_dbm / 10.0)
        self.chi = R.chi
        self.lab_chi = R.chi * sc.label_load
        self.W = R.bw_hz
        self.se_max = L.se_max
        self.bg = np.asarray(bg, dtype=float)
        self.rho = self.bg.copy()
        self.rc = self.chi * self.rho
        self.a_rho = 1.0 - np.exp(-self.mdt / L.rho_tau)
        self.tmin = SVC_TMIN[svc]
        self.thq = SVC_THQ[svc]
        self.rate = SVC_RATE[svc] * L.rate_scale
        self.gbr = SVC_GBR[svc]
        self.t0c = sc.discard
        self.is_cho = rule.kind == "cho"
        self.log = [] if log_events else None
        U, M = self.U, self.M
        self.ar = np.arange(U)
        # connection state
        self.state = np.zeros(U, dtype=np.int8)
        self.t_done = np.zeros(U)
        self.re_cell = np.zeros(U, dtype=int)
        self.serv = None
        self.meas = None
        self.prev = np.full(U, -1)
        self.last_ho = np.full(U, -1e9)
        # radio-link monitoring
        self.qo = np.zeros(U); self.qi = np.zeros(U)
        self.n_o = np.zeros(U, dtype=int); self.n_i = np.zeros(U, dtype=int)
        self.run = np.zeros(U, dtype=bool); self.t310 = np.zeros(U); self.k310 = np.zeros(U, dtype=int)
        # attempt in flight (prepared / executing)
        self.f_on = np.zeros(U, dtype=bool); self.f_t = np.zeros(U); self.f_tx = np.full(U, np.nan)
        self.f_src = np.zeros(U, dtype=int); self.f_tgt = np.zeros(U, dtype=int); self.f_key = np.full(U, -1)
        self.f_np = np.zeros(U, dtype=int); self.f_oe = np.full(U, np.nan); self.f_cnt = np.zeros(U, dtype=bool)
        # evaluation window of the last completed handover
        self.w_on = np.zeros(U, dtype=bool); self.w_t0 = np.zeros(U); self.w_ta = np.zeros(U); self.w_tx = np.zeros(U)
        self.w_src = np.zeros(U, dtype=int); self.w_tgt = np.zeros(U, dtype=int); self.w_key = np.full(U, -1)
        self.w_np = np.zeros(U, dtype=int); self.w_oe = np.full(U, np.nan); self.w_cnt = np.zeros(U, dtype=bool)
        self.w_n = np.zeros(U); self.w_g = np.zeros(U); self.w_m = np.zeros(U)
        self.w_cf = np.zeros(U); self.w_cff = np.zeros(U, dtype=bool)
        self.w_mcf = np.zeros(U); self.w_mcff = np.zeros(U, dtype=bool); self.w_pp = np.zeros(U, dtype=bool)
        # baseline handover
        self.te = np.full((U, M), INF)
        self.pend = np.zeros(U, dtype=bool); self.pend_t = np.zeros(U)
        self.n_pp, self.pp_next = 0, INF
        # conditional handover
        if self.is_cho:
            self.prepared = np.zeros((U, M), dtype=bool)
            self.ppend = np.zeros((U, M), dtype=bool); self.ppend_t = np.full((U, M), INF)
            self.oexec = np.zeros((U, M)); self.pkey = np.full((U, M), -1)
            self.tx = np.full((U, M), INF); self.tr = np.full((U, M), INF)
            self.seen = np.zeros((U, M), dtype=bool)
        self.C = {k: 0 for k in ("att", "exec", "ho", "fail", "pp", "reports", "prep_req", "cfg_ok", "cfg_lost",
                                 "prep_cancel", "prep_used", "prep_wasted", "rel", "rec", "un_and", "un_gain",
                                 "late_rlf_prepared", "att_all")}
        self.C.update({"n_" + k: 0 for k in OUTCOMES})
        self.C.update({"f_" + k: 0 for k in CAUSES})
        self.acc = dict(thr=0.0, dem=0.0, sinr=0.0, se=0.0, ncon=0, int_exec=0.0, int_fail=0.0, out_steps=0,
                        prep_time=0.0, load=0.0, nmeas=0, steps=0)
        self.wall = 0.0
        self.nmeas = 0
        rule.reset(self)

    # ------------------------------------------------------------------ logging
    def _event(self, t_att, t_x, t_end, u, kind, src, tgt, outcome, cause, dwell, gain, npr, oe, counted):
        if counted:
            self.C["n_" + outcome] = self.C.get("n_" + outcome, 0) + 1
        if self.log is not None and counted:
            k = min(int(round(t_end / self.dt)), self.S - 1)
            self.log.append((round(t_att, 4), round(t_x, 4) if t_x == t_x else -1.0, round(t_end, 4), int(u), kind,
                             int(src), int(tgt), outcome, cause, round(float(dwell), 4), round(float(gain), 3),
                             int(npr), round(float(oe), 3) if oe == oe and abs(oe) != INF else -99.0,
                             round(float(self.X[k, u]), 1), round(float(self.Y[k, u]), 1)))

    def _close_flight(self, u, t, outcome, cause):
        self._event(self.f_t[u], self.f_tx[u], t, u, self.rule.kind, self.f_src[u], self.f_tgt[u], outcome, cause,
                    0.0, 0.0, self.f_np[u], self.f_oe[u], self.f_cnt[u])
        self.f_on[u] = False
        self.pend[u] = False

    def _close_window(self, u, t, outcome, cause, dwell, gain):
        self._event(self.w_ta[u], self.w_tx[u], t, u, self.rule.kind, self.w_src[u], self.w_tgt[u], outcome, cause,
                    dwell, gain, self.w_np[u], self.w_oe[u], self.w_cnt[u])
        self.w_on[u] = False

    def _finalize(self, u, t, reason):
        """Close the evaluation window of user ``u`` ("win": complete, "ho": left by a new handover, "end")."""
        dwell = t - self.w_t0[u]
        n = max(self.w_n[u], 1.0)
        gain = self.w_g[u] / n
        short = dwell < self.tmin[u] - EPS
        if reason == "end" and short:
            self._close_window(u, t, "censored", "", dwell, gain)
            return
        low = gain < self.thq[u]
        un = (not self.w_cff[u]) and (short or low)
        if self.w_cnt[u]:
            self.C["un_and"] += int((not self.w_cff[u]) and short and low)
            self.C["un_gain"] += int((not self.w_cff[u]) and low)
        un_obs = (not self.w_mcff[u]) and (short or self.w_m[u] / n < self.thq[u])
        self.rule.on_outcome(u, int(self.w_src[u]), int(self.w_tgt[u]), int(self.w_key[u]),
                             L_UNNEC if un_obs else L_USEFUL, t)
        self._close_window(u, t, "unnecessary" if un else "useful", "", dwell, gain)

    # ------------------------------------------------------------------ procedures
    def _new_flight(self, u, tgt, t, key=-1, npr=0, oe=np.nan):
        self.f_on[u] = True
        self.f_t[u] = t
        self.f_tx[u] = np.nan
        self.f_src[u] = self.serv[u]
        self.f_tgt[u] = tgt
        self.f_key[u] = key
        self.f_np[u] = npr
        self.f_oe[u] = oe
        self.f_cnt[u] = t >= self.t0c
        self.C["att"] += int(self.f_cnt[u])
        self.C["att_all"] += 1

    def _start_exec(self, u, tgt, t):
        """The UE leaves the source cell and synchronises to ``tgt``."""
        if self.w_on[u]:
            self._finalize(u, t, "ho")
        if not self.f_on[u]:
            if self.is_cho:
                self._new_flight(u, tgt, t, self.pkey[u, tgt], int(self.prepared[u].sum()), self.oexec[u, tgt])
            else:
                self._new_flight(u, tgt, t)
        self.f_tx[u] = t
        self.state[u] = ST_EXEC
        self.t_done[u] = t + self.P.t_exec
        self.run[u] = False
        self.pend[u] = False
        if t >= self.t0c:
            self.C["exec"] += 1
            self.acc["int_exec"] += min(self.P.t_exec, self.S * self.dt - t)

    def _clear_prepared(self, u, used_cell, t):
        """Drop the conditional configurations of user ``u``; count what happened to them."""
        if not self.is_cho:
            return
        c = t >= self.t0c
        npr = int(self.prepared[u].sum())
        used = 1 if (used_cell >= 0 and self.prepared[u, used_cell]) else 0
        if c:
            self.C["prep_used"] += used
            self.C["prep_wasted"] += npr - used
            self.C["prep_cancel"] += int(self.ppend[u].sum())
        self.prepared[u] = False
        self.ppend[u] = False
        self.ppend_t[u] = INF
        self.tx[u] = INF
        self.tr[u] = INF
        self.seen[u] = False

    def _attach(self, u, cell, s, t):
        self.serv[u] = cell
        self.state[u] = ST_CONN
        self.qo[u] = self.qi[u] = s
        self.n_o[u] = self.n_i[u] = 0
        self.run[u] = False
        self.te[u] = INF

    def _end_exec(self, u, t, ln, tot):
        tgt = int(self.f_tgt[u])
        lt = ln[u, tgt]
        s = lt / (tot[u] - self.rc[tgt] * lt + self.noise)
        if s < self.qout:
            self._fail(u, t, "exec")
            return
        src = int(self.serv[u])
        pp = (self.prev[u] == tgt) and (t - self.last_ho[u] < self.P.t_pp)
        cnt = bool(self.f_cnt[u])
        if cnt:
            self.C["ho"] += 1
            self.C["pp"] += int(pp)
        self._clear_prepared(u, tgt, t)
        self.prev[u] = src
        self.last_ho[u] = t
        self._attach(u, tgt, s, t)
        # open the evaluation window
        self.w_on[u] = True; self.w_t0[u] = t; self.w_ta[u] = self.f_t[u]; self.w_tx[u] = self.f_tx[u]
        self.w_src[u] = src; self.w_tgt[u] = tgt; self.w_key[u] = self.f_key[u]
        self.w_np[u] = self.f_np[u]; self.w_oe[u] = self.f_oe[u]; self.w_cnt[u] = cnt
        self.w_n[u] = 0; self.w_g[u] = 0; self.w_m[u] = 0; self.w_cf[u] = 0; self.w_cff[u] = False
        self.w_mcf[u] = 0; self.w_mcff[u] = False; self.w_pp[u] = pp
        self.f_on[u] = False

    def _fail(self, u, t, kind):
        """Mobility failure of user ``u``: "rlf" (T310 expired), "cmd" (command lost), "exec"."""
        rule = self.rule
        c = int(np.argmax(self.meas[u]))                 # cell selected for re-establishment
        s = int(self.serv[u])
        if kind == "rlf" and self.is_cho and self.P.cfg_loss_as_hof and not self.f_on[u] and self.ppend[u].any():
            self._new_flight(u, int(np.argmax(self.ppend[u])), t)     # check mode: a pending configuration is a pending command
        if kind == "exec":
            src, tgt = int(self.f_src[u]), int(self.f_tgt[u])
            cause = "exec_fail"
            rule.on_outcome(u, src, tgt, int(self.f_key[u]), L_EARLY, t)
            self._close_flight(u, t, "early" if c in (src, tgt) else "wrong", cause)
        elif kind == "cmd":
            cause = "late_cmd"
            rule.on_outcome(u, int(self.f_src[u]), int(self.f_tgt[u]), int(self.f_key[u]), L_LATE, t)
            self._close_flight(u, t, "late", cause)
        elif self.w_on[u]:
            cause = "early_rlf"
            rule.on_outcome(u, int(self.w_src[u]), int(self.w_tgt[u]), int(self.w_key[u]), L_EARLY, t)
            dwell = t - self.w_t0[u]
            self._close_window(u, t, "early" if c in (int(self.w_src[u]), s) else "wrong", cause,
                               dwell, self.w_g[u] / max(self.w_n[u], 1.0))
            if self.f_on[u]:
                rule.on_outcome(u, int(self.f_src[u]), int(self.f_tgt[u]), int(self.f_key[u]), L_LATE, t)
                self._close_flight(u, t, "late", "late_prep")
        elif self.f_on[u]:
            cause = "late_prep"
            rule.on_outcome(u, int(self.f_src[u]), int(self.f_tgt[u]), int(self.f_key[u]), L_LATE, t)
            self._close_flight(u, t, "late", cause)
        else:
            cause = "late_rlf" if c != s else "cov_rlf"
            npr = int(self.prepared[u].sum()) if self.is_cho else 0
            if c != s:
                keys = []
                for lead in rule.late_leads:
                    k = max(0, int(self.k310[u] - round(lead / self.dt)))
                    keys.append(rule.key_at(self.X[k, u], self.Y[k, u], self.TH[k, u]))
                rule.on_late(u, s, c, keys, t)
                if npr and t >= self.t0c:
                    self.C["late_rlf_prepared"] += 1
            if self.log is not None and t >= self.t0c:
                k = min(int(round(t / self.dt)), self.S - 1)
                self.log.append((round(t, 4), -1.0, round(t, 4), int(u), "rlf", s, c,
                                 "late" if c != s else "coverage", cause, 0.0, 0.0, npr, -99.0,
                                 round(float(self.X[k, u]), 1), round(float(self.Y[k, u]), 1)))
        if t >= self.t0c:
            self.C["fail"] += 1
            self.C["f_" + cause] += 1
        rec = self.is_cho and (not rule.immediate) and bool(self.prepared[u, c])
        if rec and t >= self.t0c:
            self.C["rec"] += 1
        self._clear_prepared(u, c if rec else -1, t)
        self.state[u] = ST_REEST
        t_out = self.P.t_cho_rec if rec else self.P.t_reest
        self.t_done[u] = t + t_out
        if t >= self.t0c:
            self.acc["int_fail"] += min(t_out, self.S * self.dt - t)
        self.re_cell[u] = c
        self.run[u] = False
        self.pend[u] = False
        self.te[u] = INF

    # ------------------------------------------------------------------ main loop
    def _init(self, ch):
        self.meas = ch.l1[0].copy()
        self.serv = np.argmax(self.meas, axis=1)
        ln = ch.lin[0]
        ls = ln[self.ar, self.serv]
        s = ls / (ln @ self.rc - self.rc[self.serv] * ls + self.noise)
        self.qo[:] = s
        self.qi[:] = s

    def advance(self, ch):
        """Simulate the steps of one radio chunk."""
        w0 = time.perf_counter()
        if self.serv is None:
            self._init(ch)
        P, dt, ar = self.P, self.dt, self.ar
        state, serv, run, pend = self.state, self.serv, self.run, self.pend
        noise, qout, qin, ao, ai = self.noise, self.qout, self.qin, self.ao, self.ai
        qo, qi = self.qo, self.qi
        simple = P.n310 == 1 and P.n311 == 1
        cnz = np.count_nonzero
        lin = ch.lin
        for i in range(ch.n):
            k = ch.k0 + i
            t = k * dt
            ln = lin[i]
            tot = ln @ self.rc
            # --- end of an execution or of a re-establishment
            if cnz(state):
                for u in np.nonzero((state != ST_CONN) & (t >= self.t_done - EPS))[0]:
                    if state[u] == ST_EXEC:
                        self._end_exec(u, t, ln, tot)
                    else:
                        c = int(self.re_cell[u])
                        lc = ln[u, c]
                        self._attach(u, c, lc / (tot[u] - self.rc[c] * lc + noise), t)
            ls = ln[ar, serv]
            sinr = ls / (tot - self.rc[serv] * ls + noise)
            con = state == ST_CONN
            # --- radio-link monitoring
            qo += ao * (sinr - qo)
            qi += ai * (sinr - qi)
            if simple:
                start = (qo < qout) & con & ~run
            else:
                self.n_o = (self.n_o + 1) * (qo < qout)
                self.n_i = (self.n_i + 1) * (qi > qin)
                start = con & ~run & (self.n_o >= P.n310)
            if cnz(start):
                run |= start
                self.t310[start] = t
                self.k310[start] = k
            if cnz(run):
                run &= ~((qi > qin) if simple else (self.n_i >= P.n311))
                for u in np.nonzero(run & con & (t - self.t310 >= P.t310 - EPS))[0]:
                    self._fail(u, t, "rlf")
            # --- handover command / conditional configuration reaches the UE
            if cnz(pend):
                for u in np.nonzero(pend & (t >= self.pend_t - EPS))[0]:
                    if run[u]:
                        self._fail(u, t, "cmd")
                    else:
                        self._start_exec(u, int(self.f_tgt[u]), t)
            if self.n_pp and t >= self.pp_next - EPS:
                self._config_arrivals(t)
            # --- measurement instant
            if i % self.mp == 0:
                self._measure(ch, i // self.mp, k, t, ln)
        self.wall += time.perf_counter() - w0

    def _config_arrivals(self, t):
        rule = self.rule
        due = self.ppend & (t >= self.ppend_t - EPS)
        for u, n in zip(*np.nonzero(due)):
            if not self.ppend[u, n]:
                continue                                   # dropped by an earlier event of this step
            self.ppend[u, n] = False
            self.ppend_t[u, n] = INF
            if self.state[u] == ST_CONN and not self.run[u]:
                self.prepared[u, n] = True
                self.C["cfg_ok"] += int(t >= self.t0c)
                if rule.immediate or (rule.ttt_exec <= 0 and
                                      self.meas[u, n] - self.meas[u, self.serv[u]] > self.oexec[u, n]):
                    self._start_exec(u, int(n), t)
            else:
                self.C["cfg_lost"] += int(t >= self.t0c)
                if self.P.cfg_loss_as_hof and self.state[u] == ST_CONN:
                    self._new_flight(u, int(n), t)
                    self._fail(u, t, "cmd")
        self.n_pp = int(np.count_nonzero(self.ppend))
        self.pp_next = float(self.ppend_t.min()) if self.n_pp else INF

    def _measure(self, ch, j, k, t, ln):
        P, ar, C, acc = self.P, self.ar, self.C, self.acc
        rule, state, serv = self.rule, self.state, self.serv
        self.meas += self.a3 * (ch.l1[j] - self.meas)
        meas = self.meas
        counted = t >= self.t0c
        # --- evaluation windows (sampled every ``lab_period``)
        ia = np.nonzero(self.w_on & (state == ST_CONN))[0] if self.nmeas % self.lab_every == 0 else ()
        if len(ia):
            ldt = self.lab_every * self.mdt
            lr = ln[ia]
            lt = lr[np.arange(len(ia)), serv[ia]]
            lsrc = lr[np.arange(len(ia)), self.w_src[ia]]
            tsum = lr.sum(1)
            s_t = lt / (self.lab_chi * (tsum - lt) + self.noise)
            s_s = lsrc / (self.lab_chi * (tsum - lsrc) + self.noise)
            self.w_g[ia] += 10.0 * np.log10(s_t / s_s)
            self.w_n[ia] += 1
            self.w_cf[ia] = np.where(s_s < self.qout, self.w_cf[ia] + ldt, 0.0)
            self.w_cff[ia] |= self.w_cf[ia] >= P.t310 - EPS
            if self.learns:                                 # what the network can observe of the same quantities
                mm = meas[ia]
                ml = np.exp(mm * LN10_10)
                msrc = ml[np.arange(len(ia)), self.w_src[ia]]
                est = msrc / (self.lab_chi * (ml.sum(1) - msrc) + self.noise)
                self.w_mcf[ia] = np.where(est < self.qout, self.w_mcf[ia] + ldt, 0.0)
                self.w_mcff[ia] |= self.w_mcf[ia] >= P.t310 - EPS
                self.w_m[ia] += mm[np.arange(len(ia)), serv[ia]] - mm[np.arange(len(ia)), self.w_src[ia]]
            for u in ia[t - self.w_t0[ia] >= self.tmin[ia] - EPS]:
                self._finalize(u, t, "win")
        # --- handover rule
        con = state == ST_CONN
        gap = meas - meas[ar, serv][:, None]
        ctx = dict(t=t, k=k, meas=meas, gap=gap, serv=serv, x=self.X[k], y=self.Y[k], v=self.V, th=self.TH[k], con=con)
        if self.is_cho:
            self._cho(ctx, gap, con, t)
        else:
            off = rule.offsets(ctx)
            cond = gap > off
            cond[ar, serv] = False
            cond &= con[:, None]
            te = self.te = np.where(cond, np.minimum(self.te, t), INF)
            # the time-to-trigger timer may expire between two measurements: the report is then sent at
            # te + ttt, provided the condition held at every measurement up to now
            ready = (te + rule.ttt) < t + self.mdt - EPS
            for u in np.nonzero(ready.any(1) & ~self.pend)[0]:
                o = off[u] if isinstance(off, np.ndarray) else off
                tgt = int(np.argmax(np.where(ready[u], gap[u] - o, -INF)))
                t_rep = max(t, te[u, tgt] + rule.ttt)
                self._new_flight(u, tgt, t_rep, -1, 0, o[tgt] if isinstance(o, np.ndarray) else o)
                self.pend[u] = True
                self.pend_t[u] = t_rep + P.t_prep
                C["reports"] += int(counted)
        # --- load, scheduling, delivered rate
        con = state == ST_CONN
        ls = ln[ar, serv]
        sinr = ls / (ln @ self.rc - self.rc[serv] * ls + self.noise)
        ok = con & (sinr >= self.qout)
        se = np.minimum(np.log2(1.0 + sinr), self.se_max)
        need = np.where(ok, self.rate / (self.W * np.maximum(se, 1e-3)), 0.0)
        G = np.bincount(serv, weights=need * self.gbr, minlength=self.M)
        B = np.bincount(serv, weights=need * ~self.gbr, minlength=self.M)
        free = np.maximum(1.0 - self.bg, 0.0)
        gs = np.minimum(1.0, free / np.maximum(G, 1e-12))
        rem = np.maximum(free - G * gs, 0.0)
        bs = np.minimum(1.0, rem / np.maximum(B, 1e-12))
        thr = np.where(ok, self.rate * np.where(self.gbr, gs[serv], bs[serv]), 0.0)
        rho_new = np.minimum(1.0, self.bg + G * gs + B * bs)
        self.rho += self.a_rho * (rho_new - self.rho)
        self.rc = self.chi * self.rho
        if counted:
            acc["steps"] += self.mp
            acc["out_steps"] += self.mp * int(np.count_nonzero(con & (sinr < self.qout)))
            acc["thr"] += float(thr.sum()); acc["dem"] += float(self.rate.sum())
            acc["sinr"] += float(10.0 * np.log10(sinr[con]).sum()); acc["se"] += float(se[con].sum())
            acc["ncon"] += int(con.sum()); acc["load"] += float(rho_new.mean()); acc["nmeas"] += 1
            if self.is_cho:
                acc["prep_time"] += float(np.count_nonzero(self.prepared)) * self.mdt
        self.nmeas += 1

    def _cho(self, ctx, gap, con, t):
        P, ar, C, rule, serv = self.P, self.ar, self.C, self.rule, self.serv
        counted = t >= self.t0c
        # UE side: execution condition of the prepared cells
        if self.prepared.any():
            cx = self.prepared & (gap > self.oexec) & con[:, None]
            tx = self.tx = np.where(cx, np.minimum(self.tx, t), INF)
            rdy = (t - tx) >= rule.ttt_exec - EPS
            for u in np.nonzero(rdy.any(1))[0]:
                self._start_exec(u, int(np.argmax(np.where(rdy[u], gap[u], -INF))), t)
            con = self.state == ST_CONN
        # UE side: reporting event
        cr = gap > rule.o_rep
        cr[ar, serv] = False
        cr &= con[:, None]
        tr = self.tr = np.where(cr, np.minimum(self.tr, t), INF)
        reported = (t - tr) >= rule.ttt_prep - EPS
        fresh = reported & ~self.seen
        self.seen = reported
        if self.nmeas % self.rep == 0:                     # periodic report: every connected UE is re-evaluated
            if not (reported.any() or self.prepared.any() or self.ppend.any()):
                return
            act = con.copy()
        else:                                              # in between: only UEs with a newly triggered cell
            act = fresh.any(1)
            if not act.any():
                return
        if counted:
            C["reports"] += int(np.count_nonzero(act & reported.any(1)))
        # network side: which cells to prepare / keep / release
        score = gap - rule.prep_offsets(ctx)
        have = self.prepared | self.ppend
        elig = (reported & (score >= 0.0)) | (have & (score >= -rule.rel_hys))
        elig &= act[:, None]
        elig[ar, serv] = False
        rank = np.where(elig, score + np.where(have, rule.stick, 0.0), -INF)
        if rule.n_max < self.M:
            kth = np.partition(rank, self.M - rule.n_max, axis=1)[:, self.M - rule.n_max]
            desired = elig & (rank >= kth[:, None])
        else:
            desired = elig
        to_prep = desired & ~have
        to_rel = have & ~desired & act[:, None]
        if to_rel.any():
            if counted:
                C["prep_wasted"] += int(np.count_nonzero(to_rel & self.prepared))
                C["prep_cancel"] += int(np.count_nonzero(to_rel & self.ppend))
                C["rel"] += int(np.count_nonzero(to_rel))
            self.prepared[to_rel] = False
            self.ppend[to_rel] = False
            self.ppend_t[to_rel] = INF
            self.tx[to_rel] = INF
        if to_prep.any():
            oe = rule.exec_offsets(ctx)
            keys = rule.keys(ctx)
            uu, nn = np.nonzero(to_prep)
            self.ppend[uu, nn] = True
            self.ppend_t[uu, nn] = t + P.t_prep
            self.n_pp, self.pp_next = self.n_pp + len(uu), min(self.pp_next, t + P.t_prep)
            self.oexec[uu, nn] = oe[uu, nn] if isinstance(oe, np.ndarray) else oe
            self.pkey[uu, nn] = keys[uu] if keys is not None else -1
            if counted:
                C["prep_req"] += len(uu)

    # ------------------------------------------------------------------ results
    def finish(self):
        """Close what is still open and return the metrics of the run."""
        T = self.S * self.dt
        for u in np.nonzero(self.w_on)[0]:
            self._finalize(u, T, "end")
        for u in np.nonzero(self.f_on)[0]:
            self._close_flight(u, T, "censored", "")
        C, acc, sc = self.C, self.acc, self.sc
        umin = self.U * (sc.t_sim - sc.discard) / 60.0
        ue_s = max(acc["steps"], 1) * self.U * self.dt
        left = int(np.count_nonzero(self.prepared | self.ppend)) if self.is_cho else 0
        late = C["f_late_cmd"] + C["f_late_prep"] + C["f_late_rlf"]
        res = dict(
            rule=self.rule.name, kind=self.rule.kind, ue_min=umin,
            att_pm=C["att"] / umin, ho_pm=C["ho"] / umin, exec_pm=C["exec"] / umin,
            uho_pm=C["n_unnecessary"] / umin, uho_and_pm=C["un_and"] / umin, uho_gain_pm=C["un_gain"] / umin,
            pp_pm=C["pp"] / umin, fail_pm=C["fail"] / umin, late_pm=late / umin,
            early_pm=C["n_early"] / umin, wrong_pm=C["n_wrong"] / umin,
            prep_mean=acc["prep_time"] / ue_s, prep_req_pm=C["prep_req"] / umin,
            prep_wasted_pm=C["prep_wasted"] / umin, cfg_lost_pm=C["cfg_lost"] / umin,
            reports_pm=C["reports"] / umin, rel_pm=C["rel"] / umin, rec_pm=C["rec"] / umin,
            int_s_pm=(acc["int_exec"] + acc["int_fail"]) / umin,
            int_exec_s_pm=acc["int_exec"] / umin, int_fail_s_pm=acc["int_fail"] / umin,
            outage_pct=100.0 * (acc["int_exec"] + acc["int_fail"] + acc["out_steps"] * self.dt) / ue_s,
            rate_mbps=acc["thr"] / max(acc["nmeas"], 1) / self.U / 1e6,
            delivered=acc["thr"] / max(acc["dem"], 1e-9),
            sinr_db=acc["sinr"] / max(acc["ncon"], 1), se=acc["se"] / max(acc["ncon"], 1),
            mean_load=acc["load"] / max(acc["nmeas"], 1),
            prep_left=left, wall_s=self.wall,
        )
        for k in CAUSES:
            res["f_" + k + "_pm"] = C["f_" + k] / umin
        res["late_rlf_prepared_pm"] = C["late_rlf_prepared"] / umin
        for k in ("att", "exec", "ho", "fail", "pp", "prep_req", "cfg_ok", "cfg_lost", "prep_cancel", "prep_used",
                  "prep_wasted", "rel", "rec", "reports"):
            res["c_" + k] = C[k]
        for k in OUTCOMES:
            res["n_" + k] = C["n_" + k]
        for k in CAUSES:
            res["c_f_" + k] = C["f_" + k]
        return res
