"""Energy calibration: anchor-peak search and polynomial channel->energy fit."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks


@dataclass
class Calibration:
    """E[keV] = sum_k coeffs[k] * ch**k  (monotonic over the channel range)."""

    coeffs: np.ndarray
    n_channels: int = 4096
    anchors: list[dict] = field(default_factory=list)   # label, E_keV, ch, u_ch, residual_keV
    rms_residual_keV: float = float("nan")
    source: str = "fit"

    def __post_init__(self):
        self.coeffs = np.asarray(self.coeffs, dtype=float)
        grid = np.arange(0, self.n_channels + 1, 0.05)
        e = self.energy(grid)
        if np.any(np.diff(e) <= 0):
            raise ValueError("calibration polynomial is not monotonic over the channel range")
        self._grid, self._e = grid, e

    def energy(self, ch):
        return np.polynomial.polynomial.polyval(np.asarray(ch, dtype=float), self.coeffs)

    def channel(self, energy_keV):
        return np.interp(np.asarray(energy_keV, dtype=float), self._e, self._grid)

    def dE_dch(self, ch):
        d = np.polynomial.polynomial.polyder(self.coeffs)
        return np.polynomial.polynomial.polyval(np.asarray(ch, dtype=float), d)

    def describe(self) -> str:
        terms = " + ".join(f"{c:.6g}*ch^{k}" if k else f"{c:.6g}" for k, c in enumerate(self.coeffs))
        return f"E[keV] = {terms}"


def smooth_adaptive(counts: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Smoothing width grows with channel (NaI peak width ~ sqrt(E)); returns (smooth, sigma_s)."""
    n = counts.size
    ch = np.arange(n)
    sig = np.clip(0.02 * ch, 2.0, 40.0)
    levels = [2.0, 4.0, 8.0, 16.0, 28.0, 40.0]
    stack = np.array([gaussian_filter1d(counts.astype(float), s, mode="nearest") for s in levels])
    idx = np.abs(np.log(np.array(levels)[:, None]) - np.log(sig)[None, :]).argmin(axis=0)
    return stack[idx, ch], sig


def find_candidate_peaks(counts: np.ndarray, n_sigma: float = 4.0):
    sm, sig = smooth_adaptive(counts)
    noise = np.sqrt(np.clip(sm, 1.0, None) / (2.0 * np.sqrt(np.pi) * sig))
    peaks, props = find_peaks(sm, prominence=n_sigma * noise)
    return peaks, props["prominences"], sm


def find_anchors(counts, anchors, rough_energy, tol: float = 0.08):
    """Locate anchor peaks.

    anchors      : list of (label, E_keV[, channel_hint]) - E is the effective energy
    rough_energy : callable ch -> E  (e.g. the header calibration, may be off by a few %)
    Returns list of dict(label, E_keV, ch, prominence) for anchors found.
    """
    peaks, prom, _ = find_candidate_peaks(counts)
    e_pk = rough_energy(peaks)
    found = []
    for a in anchors:
        label, e_nom = a[0], float(a[1])
        hint = a[2] if len(a) > 2 else None
        if hint is not None:
            sel = np.abs(peaks - hint) <= max(10, 0.03 * hint)
        else:
            sel = np.abs(e_pk / e_nom - 1.0) <= tol
        if not sel.any():
            continue
        k = np.flatnonzero(sel)[np.argmax(prom[sel])]
        found.append({"label": label, "E_keV": e_nom, "ch": float(peaks[k]), "prominence": float(prom[k])})
    return found


def fit_calibration(points, order: int = 2, n_channels: int = 4096, source: str = "fit") -> Calibration:
    """Weighted polynomial fit.  points: list of dict(label, E_keV, ch, u_ch) (u_ch optional)."""
    ch = np.array([p["ch"] for p in points], dtype=float)
    e = np.array([p["E_keV"] for p in points], dtype=float)
    u = np.array([p.get("u_ch", 1.0) or 1.0 for p in points], dtype=float)
    order = int(min(order, len(points) - 1))
    if order < 1:
        raise ValueError("need at least two anchor peaks for an energy calibration")
    # fit ch -> E; weights from the channel uncertainty propagated with the local slope
    slope0 = np.gradient(e, ch) if len(ch) > 1 else np.ones_like(e)
    w = 1.0 / np.clip(u * np.abs(slope0), 1e-3, None)
    coeffs = np.polynomial.polynomial.polyfit(ch, e, order, w=w)
    res = e - np.polynomial.polynomial.polyval(ch, coeffs)
    out = []
    for p, r in zip(points, res):
        q = dict(p)
        q["residual_keV"] = float(r)
        out.append(q)
    dof = max(1, len(points) - order - 1)
    rms = float(np.sqrt(np.sum(res**2) / dof)) if len(points) > order + 1 else float(np.sqrt(np.mean(res**2)))
    return Calibration(coeffs, n_channels=n_channels, anchors=out, rms_residual_keV=rms, source=source)
