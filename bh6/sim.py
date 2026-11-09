# -*- coding: utf-8 -*-
"""Building a simulated world and running handover rules on it.

A *world* is everything that a seed fixes: layout, radio map, trajectories,
services and background load.  :func:`run_rules` runs any number of rules on
the same world and the same radio samples (common random numbers), which is
what makes the comparison of rules paired by seed.
"""
import time
from dataclasses import dataclass

import numpy as np

from .backend import NumpyOps
from .engine import Engine
from .layout import make_layout
from .mobility import gen_traj
from .policies import make_rule
from .radio import RadioMap, RadioSource, _streams
from .services import assign_services


@dataclass
class World:
    sc: object
    layout: object
    rmap: object
    traj: tuple
    svc: np.ndarray
    bg: np.ndarray


def build_world(sc, ops=None):
    """Create layout, radio map, trajectories, services and background load of a scenario."""
    layout = make_layout(sc)
    rng_traj, rng_svc, rng_bg = _streams(sc.seed * 1000003 + 3, 3)
    rmap = RadioMap(layout, sc.radio, sc.seed, ops or NumpyOps(), clutter=sc.clutter)
    traj = gen_traj(layout, sc, rng_traj)
    svc = assign_services(sc.n_ue, rng_svc)
    M, L = layout.M, sc.load
    hot = np.zeros(M, dtype=bool)
    hot[rng_bg.choice(M, max(1, int(round(L.hot_frac * M))), replace=False)] = True
    bg = np.where(hot, rng_bg.uniform(*L.bg_hot, M), rng_bg.uniform(*L.bg_norm, M))
    return World(sc, layout, rmap, traj, svc, bg)


def run_rules(sc, specs, ops=None, log_events=False, world=None, timing=None):
    """Run the rules described by ``specs`` on one world.

    ``specs``: list of rule descriptions (see :func:`bh6.policies.make_rule`).
    Returns ``(results, engines)``; ``results[i]`` is the metric dictionary of
    ``specs[i]``.  ``timing``, if a dict, receives the seconds spent on the
    radio map, the radio samples and the engines.
    """
    t0 = time.perf_counter()
    w = world or build_world(sc, ops)
    t1 = time.perf_counter()
    src = RadioSource(w.rmap, w.traj, sc)
    engines = [Engine(sc, w.layout, w.rmap, w.traj, w.svc, w.bg, make_rule(s), log_events) for s in specs]
    t_radio = 0.0
    it = src.chunks()
    while True:
        ta = time.perf_counter()
        ch = next(it, None)
        t_radio += time.perf_counter() - ta
        if ch is None:
            break
        for e in engines:
            e.advance(ch)
    res = [e.finish() for e in engines]
    if timing is not None:
        timing.update(map_s=t1 - t0, radio_s=t_radio, engine_s=sum(e.wall for e in engines),
                      total_s=time.perf_counter() - t0, device=getattr(w.rmap.ops, "device", "cpu"),
                      backend=w.rmap.ops.name)
    return res, engines
