"""Poisson peak fitting of Gaussian line groups on a polynomial + Compton-edge background.

* Peaks are fitted by minimising the Poisson deviance (maximum likelihood);
  parameter covariance comes from the Fisher information matrix of the Poisson
  model, inflated by sqrt(chi2/ndf) when the fit is poorer than statistics allow.
* A *line group* is one or more gamma lines that the detector cannot resolve
  (e.g. Ba-133 356+384 keV).  They share one amplitude/centroid/width with the
  relative intensities and energy offsets fixed from nuclear data.
* ``compton_edges_keV`` adds a smeared step (erfc) at the Compton edge of a
  higher-energy line that sits inside the window (e.g. 1332 keV edge at 1118 keV
  under the 1173 keV peak).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np
from scipy.optimize import least_squares
from scipy.special import erfc, ndtr

from .calibration import Calibration

ME_C2_KEV = 510.99895


# --------------------------------------------------------------------------- specs
@dataclass(frozen=True)
class PeakSpec:
    label: str
    energies: tuple[float, ...]
    weights: tuple[float, ...] = (1.0,)
    reported: bool = True          # False -> nuisance component, never used for LAC
    free_E_keV: float | None = None  # allowed centroid excursion (keV); None -> from resolution
    source: str = ""
    step: bool = False             # add a smeared low-energy step (multiple-scatter plateau) under the peak
    sigma_range: tuple[float, float] = (0.6, 1.5)   # allowed width relative to the resolution law

    def __post_init__(self):
        w = np.asarray(self.weights, dtype=float)
        object.__setattr__(self, "weights", tuple((w / w.sum()).tolist()))

    @property
    def E_main(self) -> float:
        return self.energies[int(np.argmax(self.weights))]

    @property
    def E_eff(self) -> float:
        return float(np.dot(self.energies, self.weights))


@dataclass(frozen=True)
class RegionSpec:
    name: str
    lo_keV: float
    hi_keV: float
    peaks: tuple[PeakSpec, ...]
    bkg_order: int = 1
    compton_edges_keV: tuple[float, ...] = ()
    tie_sigma: bool = False        # sigma_k = sigma_0 * sqrt(E_k / E_0)


@dataclass
class Resolution:
    """Gaussian sigma in keV: sigma(E) = k * (E/662)^p, FWHM = 2.3548 sigma.

    Defaults are typical for a NaI(Tl) detector (7.5 % FWHM at 662 keV, FWHM ~ E^0.65);
    the pipeline re-estimates both numbers from the fitted peaks of every spectrum.
    """

    k: float = 0.075 * 661.66 / 2.3548
    p: float = 0.65

    def sigma_keV(self, E):
        return self.k * (np.asarray(E, dtype=float) / 661.66) ** self.p

    def fwhm_percent(self, E):
        return 100.0 * 2.3548 * self.sigma_keV(E) / np.asarray(E, dtype=float)

    @classmethod
    def from_points(cls, energies, sigmas_keV, default: "Resolution | None" = None):
        """Least-squares power-law through (E, sigma) pairs; falls back to ``default``."""
        e, sg = np.asarray(energies, float), np.asarray(sigmas_keV, float)
        ok = np.isfinite(e) & np.isfinite(sg) & (sg > 0)
        default = default or cls()
        if ok.sum() < 3 or np.ptp(np.log(e[ok])) < 0.7:
            return default
        p, lk = np.polyfit(np.log(e[ok] / 661.66), np.log(sg[ok]), 1)
        p = float(np.clip(p, 0.3, 1.0))
        lk = float(np.mean(np.log(sg[ok]) - p * np.log(e[ok] / 661.66)))
        return cls(k=float(np.exp(lk)), p=p)


@dataclass
class RegionFit:
    region: RegionSpec
    ok: bool
    message: str
    ch_lo: int
    ch_hi: int
    x: np.ndarray
    y: np.ndarray
    model: np.ndarray | None = None
    background: np.ndarray | None = None
    chi2: float = float("nan")          # Pearson chi2
    deviance: float = float("nan")
    ndf: int = 0
    birge: float = 1.0
    peaks: dict = field(default_factory=dict)   # label -> dict(area,u_area,u_area_stat,mu,sigma,...)
    params: dict = field(default_factory=dict)
    window_scale: float = 1.0
    bkg_order: int = 1

    @property
    def chi2_red(self) -> float:
        return self.chi2 / self.ndf if self.ndf > 0 else float("nan")


# --------------------------------------------------------------------------- model
def _gauss_bin(x, mu, sig):
    return ndtr((x + 0.5 - mu) / sig) - ndtr((x - 0.5 - mu) / sig)


class _Layout:
    """Parameter vector layout + model evaluation for one region."""

    def __init__(self, region: RegionSpec, cal: Calibration, ch_lo: int, ch_hi: int, bkg_order: int):
        self.region, self.cal = region, cal
        self.x = np.arange(ch_lo, ch_hi, dtype=float)
        self.xmid = 0.5 * (ch_lo + ch_hi - 1)
        self.xhalf = 0.5 * (ch_hi - ch_lo)
        self.bkg_order = bkg_order
        self.free_sigma = [not (region.tie_sigma and k > 0) for k in range(len(region.peaks))]
        names = []
        for k, p in enumerate(region.peaks):
            names += [f"A[{k}]", f"mu[{k}]"] + ([f"sigma[{k}]"] if self.free_sigma[k] else [])
            if p.step:
                names.append(f"step[{k}]")
        names += [f"b{j}" for j in range(bkg_order + 1)]
        names += [f"edge[{j}]" for j in range(len(region.compton_edges_keV))]
        self.names = names
        self.idx = {n: i for i, n in enumerate(names)}
        # channel offsets of the extra components of a group (fixed from calibration)
        self.comp_dch = []
        self.edge_ch = [
            float(cal.channel(e - e / (1.0 + 2.0 * e / ME_C2_KEV))) for e in region.compton_edges_keV]

    def peak_pars(self, theta, k):
        p = self.region.peaks[k]
        A, mu = theta[self.idx[f"A[{k}]"]], theta[self.idx[f"mu[{k}]"]]
        if self.free_sigma[k]:
            sig = theta[self.idx[f"sigma[{k}]"]]
        else:
            s0 = theta[self.idx["sigma[0]"]]
            p0 = self.region.peaks[0]
            sig = s0 * np.sqrt(p.E_main / p0.E_main) * self._res_ratio(0, k, mu)
        return A, mu, sig

    @staticmethod
    def _res_ratio(i, k, mu):  # hook for non-sqrt laws; identity here
        return 1.0

    def components(self, theta, k):
        p = self.region.peaks[k]
        A, mu, sig = self.peak_pars(theta, k)
        slope = float(self.cal.dE_dch(mu)) or 1.0
        out = []
        for E, w in zip(p.energies, p.weights):
            out.append((A * w, mu + (E - p.E_main) / slope, sig * np.sqrt(E / p.E_main)))
        return out

    def background(self, theta):
        t = (self.x - self.xmid) / self.xhalf
        b = np.zeros_like(self.x)
        for j in range(self.bkg_order + 1):
            b += theta[self.idx[f"b{j}"]] * t**j
        for k, p in enumerate(self.region.peaks):
            if p.step:
                _, mu, sig = self.peak_pars(theta, k)
                b += theta[self.idx[f"step[{k}]"]] * 0.5 * erfc((self.x - mu) / (np.sqrt(2.0) * sig))
        for j, ech in enumerate(self.edge_ch):
            # width: use the first peak's resolution scaled to the edge energy
            _, _, s0 = self.peak_pars(theta, 0)
            e_edge = float(self.cal.energy(ech))
            sig_e = s0 * np.sqrt(max(e_edge, 1.0) / self.region.peaks[0].E_main)
            b += theta[self.idx[f"edge[{j}]"]] * 0.5 * erfc((self.x - ech) / (np.sqrt(2.0) * sig_e))
        return b

    def peak_curve(self, theta, k):
        y = np.zeros_like(self.x)
        for a, mu, sig in self.components(theta, k):
            y += a * _gauss_bin(self.x, mu, sig)
        return y

    def model(self, theta):
        m = self.background(theta)
        for k in range(len(self.region.peaks)):
            m = m + self.peak_curve(theta, k)
        return m


def _deviance_residuals(y, m):
    m = np.clip(m, 1e-9, None)
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(y > 0, y * np.log(y / m), 0.0)
    d = 2.0 * (m - y + term)
    return np.sign(y - m) * np.sqrt(np.clip(d, 0.0, None))


def _num_jac(f, theta, rel=1e-6):
    f0 = f(theta)
    J = np.empty((f0.size, theta.size))
    for i in range(theta.size):
        h = rel * max(abs(theta[i]), 1.0)
        tp, tm = theta.copy(), theta.copy()
        tp[i] += h
        tm[i] -= h
        J[:, i] = (f(tp) - f(tm)) / (2 * h)
    return J


# --------------------------------------------------------------------------- fitting
def fit_region(counts, cal: Calibration, region: RegionSpec, res: Resolution, *,
               window_scale: float = 1.0, bkg_order: int | None = None) -> RegionFit:
    counts = np.asarray(counts, dtype=float)
    p_order = region.bkg_order if bkg_order is None else bkg_order
    c_lo, c_hi = float(cal.channel(region.lo_keV)), float(cal.channel(region.hi_keV))
    cen, half = 0.5 * (c_lo + c_hi), 0.5 * (c_hi - c_lo) * window_scale
    ch_lo, ch_hi = int(max(0, round(cen - half))), int(min(counts.size, round(cen + half)))
    lay = _Layout(region, cal, ch_lo, ch_hi, p_order)
    y = counts[ch_lo:ch_hi]
    n = y.size

    # ---- seeds & bounds -------------------------------------------------------------
    theta0, lo, hi = [], [], []
    for k, p in enumerate(region.peaks):
        mu0 = float(cal.channel(p.E_main))
        slope = float(cal.dE_dch(mu0))
        sig0 = float(res.sigma_keV(p.E_main)) / slope
        exc = (p.free_E_keV if p.free_E_keV is not None else 1.5 * res.sigma_keV(p.E_main)) / slope
        # crude amplitude: counts within +-1.2 sigma above a local linear baseline
        sel = np.abs(lay.x - mu0) <= 1.2 * sig0
        base = np.interp(lay.x, [lay.x[0], lay.x[-1]],
                         [y[:max(3, n // 15)].mean(), y[-max(3, n // 15):].mean()])
        a0 = max(float((y[sel] - base[sel]).sum()) / 0.77, 10.0) if sel.any() else 10.0
        theta0 += [a0, mu0]
        lo += [-5.0 * abs(a0) - 1e3, mu0 - exc]
        hi += [5.0 * abs(a0) + 1e5, mu0 + exc]
        if lay.free_sigma[k]:
            theta0.append(sig0)
            lo.append(p.sigma_range[0] * sig0)
            hi.append(p.sigma_range[1] * sig0)
        if p.step:
            theta0.append(0.0)
            lo.append(-1.0 * float(y.mean()))
            hi.append(3.0 * float(y.mean()))
    ybar = float(y.mean())
    for j in range(p_order + 1):
        theta0.append(ybar if j == 0 else 0.0)
        lo.append(-10 * ybar - 10 if j == 0 else -20 * ybar - 10)
        hi.append(10 * ybar + 10 if j == 0 else 20 * ybar + 10)
    for _ in region.compton_edges_keV:
        theta0.append(0.0)
        lo.append(-5 * ybar - 10)
        hi.append(5 * ybar + 10)
    theta0, lo, hi = np.array(theta0), np.array(lo), np.array(hi)
    theta0 = np.clip(theta0, lo + 1e-9, hi - 1e-9)

    def resid(th):
        return _deviance_residuals(y, lay.model(th))

    try:
        sol = least_squares(resid, theta0, bounds=(lo, hi), x_scale="jac", max_nfev=400)
    except Exception as exc:  # pragma: no cover - defensive
        return RegionFit(region, False, f"optimizer error: {exc}", ch_lo, ch_hi, lay.x, y,
                         window_scale=window_scale, bkg_order=p_order)
    th = sol.x
    m = lay.model(th)
    mc = np.clip(m, 1e-9, None)
    pearson = float(np.sum((y - m) ** 2 / mc))
    dev = float(np.sum(_deviance_residuals(y, m) ** 2))
    free = np.flatnonzero((th > lo + 1e-7 * (hi - lo)) & (th < hi - 1e-7 * (hi - lo)))
    at_bound = [lay.names[i] for i in range(th.size) if i not in set(free.tolist())]
    ndf = n - th.size

    # ---- covariance from the Poisson Fisher information --------------------------------
    J = _num_jac(lambda t: lay.model(t), th)
    Jf = J[:, free]
    fisher = Jf.T @ (Jf / mc[:, None])
    ok, msg = True, "ok"
    try:
        covf = np.linalg.inv(fisher)
        if not np.all(np.isfinite(covf)) or np.any(np.diag(covf) < 0):
            raise np.linalg.LinAlgError("non positive-definite covariance")
    except np.linalg.LinAlgError:
        covf = np.full((free.size, free.size), np.nan)
        ok, msg = False, "singular Fisher matrix"
    cov = np.full((th.size, th.size), np.nan)
    cov[np.ix_(free, free)] = covf
    birge = float(np.sqrt(max(1.0, pearson / ndf))) if ndf > 0 else 1.0
    cov_s = cov * birge**2

    peaks = {}
    for k, p in enumerate(region.peaks):
        iA, iMu = lay.idx[f"A[{k}]"], lay.idx[f"mu[{k}]"]
        A, mu, sig = lay.peak_pars(th, k)
        uA_stat = float(np.sqrt(cov[iA, iA])) if np.isfinite(cov[iA, iA]) else float("nan")
        uA = float(np.sqrt(cov_s[iA, iA])) if np.isfinite(cov_s[iA, iA]) else float("nan")
        peaks[p.label] = {
            "area": float(A), "u_area": uA, "u_area_stat": uA_stat,
            "mu_ch": float(mu), "u_mu_ch": float(np.sqrt(cov_s[iMu, iMu])) if np.isfinite(cov_s[iMu, iMu]) else float("nan"),
            "sigma_ch": float(sig), "E_main": p.E_main, "E_eff": p.E_eff,
            "reported": p.reported, "curve": lay.peak_curve(th, k)}
    fit = RegionFit(region, ok, msg, ch_lo, ch_hi, lay.x, y, model=m, background=lay.background(th),
                    chi2=pearson, deviance=dev, ndf=ndf, birge=birge, peaks=peaks,
                    params=dict(zip(lay.names, th.tolist())), window_scale=window_scale, bkg_order=p_order)
    if at_bound:
        fit.message = ("ok; at bound: " + ",".join(at_bound)) if ok else msg + "; at bound: " + ",".join(at_bound)
    return fit


def roi_sum_area(counts, ch_lo: int, ch_hi: int, n_bkg: int = 8):
    """Classical net area: gross ROI counts minus linear background from ``n_bkg`` edge channels
    (Gilmore, Practical Gamma-ray Spectrometry).  Returns (net, u_net)."""
    counts = np.asarray(counts, dtype=float)
    g = counts[ch_lo:ch_hi].sum()
    n = ch_hi - ch_lo
    left, right = counts[ch_lo:ch_lo + n_bkg].sum(), counts[ch_hi - n_bkg:ch_hi].sum()
    b = n / (2.0 * n_bkg) * (left + right)
    u2 = g + (n / (2.0 * n_bkg)) ** 2 * (left + right)
    return float(g - b), float(np.sqrt(u2))
