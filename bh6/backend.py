# -*- coding: utf-8 -*-
"""Array back-ends for the deterministic radio computations.

Only the *deterministic* part of the radio model (line-of-sight geometry, path
loss, interpolation of the radio map, dB conversions) goes through a back-end.
Every random number is drawn with NumPy on the CPU, whatever the back-end, so a
run uses the same random streams on every device.

``NumpyOps`` is the reference.  ``TorchOps`` runs the same formulas through
PyTorch on ``cpu`` or ``cuda``.  Whether the PyTorch path is used is decided by
``selftest_backend.py`` on the machine that runs the study (it must reproduce
the NumPy numbers and be faster); see :func:`choose_ops`.
"""
import json
import os

import numpy as np


class NumpyOps:
    """Reference implementation (float64 geometry, float32 maps)."""
    name = "numpy"
    device = "cpu"

    def arr(self, a, dtype="f8"):
        return np.asarray(a, dtype=dtype)

    def out(self, a):
        return np.asarray(a)

    def sqrt(self, a):
        return np.sqrt(a)

    def log10(self, a):
        return np.log10(a)

    def pow10(self, a):
        return np.power(10.0, a)

    def where(self, c, a, b):
        return np.where(c, a, b)

    def maximum(self, a, b):
        return np.maximum(a, b)

    def minimum(self, a, b):
        return np.minimum(a, b)

    def abs(self, a):
        return np.abs(a)

    def floor_int(self, a):
        return np.floor(a).astype(np.int64)

    def take(self, a, idx):
        return np.take(a, idx, axis=0)

    def sync(self):
        pass


class TorchOps:
    """The same operations through PyTorch (``device`` = "cpu" or "cuda")."""
    name = "torch"

    def __init__(self, device="cuda"):
        import torch
        self.t = torch
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but torch.cuda.is_available() is False")
        self.device = device
        self._dt = {"f8": torch.float64, "f4": torch.float32, "i8": torch.int64, "?": torch.bool}

    def arr(self, a, dtype="f8"):
        t = self.t
        if isinstance(a, t.Tensor):
            return a.to(device=self.device, dtype=self._dt[dtype])
        return t.as_tensor(np.asarray(a), dtype=self._dt[dtype], device=self.device)

    def out(self, a):
        return a.detach().cpu().numpy()

    def _t(self, a, like):
        t = self.t
        return a if isinstance(a, t.Tensor) else t.as_tensor(a, dtype=like.dtype, device=like.device)

    def sqrt(self, a):
        return self.t.sqrt(a)

    def log10(self, a):
        return self.t.log10(a)

    def pow10(self, a):
        return self.t.pow(10.0, a)

    def where(self, c, a, b):
        t = self.t
        ref = a if isinstance(a, t.Tensor) else b
        return t.where(c, self._t(a, ref), self._t(b, ref))

    def maximum(self, a, b):
        t = self.t
        ref = a if isinstance(a, t.Tensor) else b
        return t.maximum(self._t(a, ref), self._t(b, ref))

    def minimum(self, a, b):
        t = self.t
        ref = a if isinstance(a, t.Tensor) else b
        return t.minimum(self._t(a, ref), self._t(b, ref))

    def abs(self, a):
        return self.t.abs(a)

    def floor_int(self, a):
        return self.t.floor(a).to(self.t.int64)

    def take(self, a, idx):
        return a.index_select(0, idx)

    def sync(self):
        if self.device.startswith("cuda"):
            self.t.cuda.synchronize()


CHOICE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend_choice.json")


def make_ops(device="cpu"):
    """Return the back-end for ``device``: "cpu" (NumPy), "torch-cpu" or "cuda"."""
    device = (device or "cpu").lower()
    if device in ("cpu", "numpy"):
        return NumpyOps()
    if device == "torch-cpu":
        return TorchOps("cpu")
    if device.startswith("cuda") or device == "gpu":
        return TorchOps("cuda" if device == "gpu" else device)
    raise ValueError("unknown device %r (use cpu, torch-cpu, cuda or auto)" % device)


def resolve_device(device="auto"):
    """Turn ``auto`` into the device verified by ``selftest_backend.py``.

    ``auto`` gives "cpu" unless the self-test has written ``backend_choice.json``
    with another verified and faster device.  An explicit device is returned
    unchanged; if it cannot be created the caller falls back to NumPy.
    """
    device = (device or os.environ.get("BH6_DEVICE") or "auto").lower()
    if device != "auto":
        return device
    try:
        with open(CHOICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("device", "cpu")
    except (OSError, ValueError):
        return "cpu"


def choose_ops(device="auto"):
    """Back-end for ``device`` with a silent fall-back to NumPy."""
    dev = resolve_device(device)
    try:
        return make_ops(dev)
    except Exception:           # PyTorch missing, no CUDA, driver trouble: the reference path always works
        return NumpyOps()
