# -*- coding: utf-8 -*-
"""Parameter sets of the simulator.

All physical and protocol constants live here so that a scenario is fully
described by one :class:`Scenario` object (and therefore by one JSON record in
the result files).  Defaults describe the main condition of the study: an
ultra-dense street deployment in the upper mid-band (10 GHz carrier).
"""
from dataclasses import dataclass, field, asdict, replace
import math


@dataclass
class Radio:
    """Carrier, link budget, shadowing and the antenna abstraction."""
    fc_ghz: float = 10.0        # carrier frequency [GHz]
    bw_hz: float = 200e6        # carrier bandwidth [Hz]
    tx_dbm: float = 35.0        # total transmit power per site [dBm]
    g_bs_db: float = 20.0       # peak beamforming gain of the site towards a served/measured UE [dB]
    g_ue_db: float = 0.0        # UE antenna gain [dBi]
    nf_db: float = 7.0          # UE noise figure [dB]
    chi: float = 0.30           # mean-to-peak gain ratio of an interfering data beam (isolation, about -5 dB)
    h_bs: float = 10.0          # site height [m]
    h_ut: float = 1.5           # UE height [m]
    pl_model: str = "umi"       # "umi" (TR 38.901 UMi street canyon) or "uma"
    sf_los: float = 4.0         # shadow-fading std, LOS [dB]   (TR 38.901 Table 7.4.1-1, UMi)
    sf_nlos: float = 7.82       # shadow-fading std, NLOS [dB]
    d_corr: float = 10.0        # shadow-fading decorrelation distance [m]
    xcorr: float = 0.5          # correlation of the shadowing between sites
    place_share: float = 1.0    # share of the shadowing variance that is tied to place (shared static field);
                                # the rest is a process along each UE's own path (not repeatable by place)
    sigma_t: float = 1.5        # time-varying component (moving blockers) [dB]
    tau_t: float = 1.0          # its correlation time [s]
    meas_sigma: float = 1.0     # error of one L1 RSRP sample [dB]
    map_res: float = 1.0        # resolution of the radio map [m]
    los_corr: float = 50.0      # correlation distance of the LOS state in the open environment [m]

    @property
    def noise_dbm(self):
        """Thermal noise over the carrier plus the noise figure [dBm]."""
        return -174.0 + 10.0 * math.log10(self.bw_hz) + self.nf_db


@dataclass
class Proto:
    """Measurement chain, handover timing and the failure model.

    Failure parameters follow 3GPP TR 36.839 (Qout -8 dB, Qin -6 dB, T310 1 s,
    N310 = N311 = 1, preparation 50 ms, execution 40 ms).
    """
    dt: float = 0.01            # simulation step [s]
    meas_period: float = 0.04   # period of L1 samples entering the L3 filter [s]
    l3_k: int = 4               # L3 filter coefficient k (reference sample period 200 ms, TS 38.331 5.5.3.2)
    lab_period: float = 0.2     # sampling period of the outcome-label quantities [s]
    report_interval: float = 0.12   # periodic re-reporting while an event stays fulfilled (reportInterval ms120)
    qout_db: float = -8.0
    qin_db: float = -6.0
    qout_win: float = 0.2       # evaluation window of Qout [s]
    qin_win: float = 0.1        # evaluation window of Qin [s]
    n310: int = 1
    n311: int = 1
    t310: float = 1.0
    t_prep: float = 0.05        # handover preparation (report -> command / conditional configuration at the UE) [s]
    t_exec: float = 0.04        # handover execution = interruption [s]
    t_reest: float = 1.0        # outage of an RRC re-establishment after a failure [s]
    t_cho_rec: float = 0.4      # outage when the UE recovers into a prepared cell (Rel-16 CHO recovery) [s]
    t_pp: float = 1.0           # ping-pong window (minimum time of stay, TR 36.839) [s]
    cfg_loss_as_hof: bool = False   # treat a lost conditional configuration like a lost handover command (checks only)


@dataclass
class Load:
    """Traffic and background load (same structure as the group's earlier simulator)."""
    se_max: float = 7.4         # spectral-efficiency cap [bit/s/Hz]
    hot_frac: float = 0.25      # share of hotspot cells
    bg_hot: tuple = (0.55, 0.85)
    bg_norm: tuple = (0.05, 0.25)
    rho_tau: float = 0.2        # smoothing time of the cell load [s]
    rate_scale: float = 1.0     # multiplies every service rate


@dataclass
class Scenario:
    """One simulated condition.  ``seed`` selects environment, trajectories and noise."""
    name: str = "grid"
    env: str = "grid"           # "grid" (street grid with buildings) or "open" (no place-tied blockage)
    isd: float = 100.0          # site distance along the streets [m]
    profile: str = "veh16"      # mobility profile, see mobility.PROFILES
    n_ue: int = 60
    t_sim: float = 420.0        # run length [s]
    discard: float = 60.0       # initial part not counted [s]
    seed: int = 1
    clutter: bool = True        # in-street obstacles: spatially consistent LOS state of TR 38.901 on top of the buildings
    sites: tuple = None         # explicit site list ((x, y), ...) overrides the regular placement
    site_offset: float = 9.0    # lateral distance of a site from the street centre line [m]
    label_load: float = 1.0     # load assumed for the SINR used by the outcome label (1 = all cells transmit)
    radio: Radio = field(default_factory=Radio)
    proto: Proto = field(default_factory=Proto)
    load: Load = field(default_factory=Load)

    def to_dict(self):
        return asdict(self)

    def with_(self, **kw):
        """Copy with changed fields; keys ``radio__x`` / ``proto__x`` / ``load__x`` reach the nested sets."""
        top, sub = {}, {"radio": {}, "proto": {}, "load": {}}
        for k, v in kw.items():
            if "__" in k:
                a, b = k.split("__", 1)
                sub[a][b] = v
            else:
                top[k] = v
        sc = replace(self, **top)
        for a, d in sub.items():
            if d:
                setattr(sc, a, replace(getattr(sc, a), **d))
        return sc
