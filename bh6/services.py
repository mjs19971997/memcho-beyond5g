# -*- coding: utf-8 -*-
"""Service classes (5QI values of 3GPP TS 23.501, Table 5.7.4-1).

The outcome label of a handover depends on the service of the user: ``t_min``
is the minimum useful time of stay in the target and ``theta_q`` the minimum
quality gain.  These two columns and the population shares are the same as in
the group's earlier studies, so that the label keeps its meaning.  The rates
are raised to values typical for the traffic expected in the upper mid-band.
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Service:
    key: str
    fiveqi: int
    gbr: bool
    t_min: float      # minimum useful time of stay [s]
    theta_q: float    # minimum mean SINR gain [dB]
    w_int: float      # weight of an interruption (used by the per-user margin rule)
    share: float      # share of the users
    rate_mbps: float  # demanded rate [Mbit/s]


SERVICES = [
    Service("voice", 1, True, 4.0, 0.7, 0.35, 0.20, 0.1),
    Service("vcall", 2, True, 6.0, 1.0, 0.55, 0.20, 4.0),
    Service("gaming", 3, True, 7.0, 1.2, 0.70, 0.15, 30.0),
    Service("stream", 6, False, 3.0, 1.5, 0.20, 0.30, 25.0),
    Service("web", 9, False, 2.0, 0.4, 0.10, 0.15, 10.0),
]
SVC_KEYS = [s.key for s in SERVICES]
SVC_TMIN = np.array([s.t_min for s in SERVICES])
SVC_THQ = np.array([s.theta_q for s in SERVICES])
SVC_W = np.array([s.w_int for s in SERVICES])
SVC_GBR = np.array([s.gbr for s in SERVICES])
SVC_RATE = np.array([s.rate_mbps for s in SERVICES]) * 1e6
SVC_SHARE = np.array([s.share for s in SERVICES])


def assign_services(n_ue, rng):
    """Draw a service index for every user according to the population shares."""
    p = SVC_SHARE / SVC_SHARE.sum()
    return rng.choice(len(SERVICES), size=n_ue, p=p)
