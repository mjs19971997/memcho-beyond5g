# -*- coding: utf-8 -*-
"""bh6: system-level simulator for handover control in ultra-dense upper-mid-band networks.

Modules
    params     parameter sets (radio, protocol, load, scenario)
    pathloss   3GPP TR 38.901 path loss (UMi street canyon, UMa)
    layout     street grid with buildings / open area, line-of-sight geometry
    radio      radio map (place-tied) and per-run radio samples
    mobility   mobility profiles and trajectories
    policies   handover rules (A3, per-user margin, conditional handover, memory-steered conditional handover)
    engine     measurement chain, handover procedures, failures, outcome labels
    sim        building a world and running rules on it
    study      scenarios, tuning spaces, stages and jobs of the study
    stats      paired tests and intervals
    backend    NumPy / PyTorch back-ends of the deterministic radio computations
"""
__version__ = "1.0.0"
