"""Gamma shielding parameters with first-order (GUM) uncertainty propagation.

Notation
--------
L = ln(I0/I)               attenuation exponent of the sample (I = net peak count rate)
mu   = L / x               linear attenuation coefficient (LAC)      [cm^-1]
mu_m = mu / rho            mass attenuation coefficient (MAC)        [cm^2/g]
HVL = ln2/mu, TVL = ln10/mu, MFP = 1/mu                              [cm]
RPE = (1 - I/I0) * 100     radiation protection efficiency           [%]
Zeff = sigma_a / sigma_e   effective atomic number (direct method)
Neff = mu_m / sigma_e      effective electron number                 [electrons/g]
Ne   = Neff * rho          electron density                          [electrons/cm^3]
sigma_a = mu_m / (N_A * sum_i w_i/A_i)       total atomic cross section [cm^2/atom]
sigma_e = (1/N_A) sum_i f_i (A_i/Z_i) (mu/rho)_i   electronic cross section [cm^2/electron]

Inputs I0, I, x and rho are treated as independent.  Uncertainties of the elemental
(mu/rho)_i entering sigma_e are not propagated (optional relative term
``xs_rel_uncertainty`` is added to the theoretical values only).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .xsec import ELEMENTS, CrossSections, mixture_mass_attenuation

N_A = 6.02214076e23
BARN = 1e-24
LN2, LN10 = math.log(2.0), math.log(10.0)


# --------------------------------------------------------------------------- inputs
@dataclass
class Quantity:
    value: float
    u: float = 0.0

    def __iter__(self):
        yield self.value
        yield self.u


def mean_with_sem(values, instrument_u: float = 0.0) -> Quantity:
    """Mean of repeated readings; u = sqrt(SEM^2 + instrument_u^2).  One reading -> u = instrument_u."""
    v = np.asarray(values, dtype=float).ravel()
    v = v[np.isfinite(v)]
    if v.size == 0:
        return Quantity(float("nan"), float("nan"))
    sem = float(np.std(v, ddof=1) / math.sqrt(v.size)) if v.size > 1 else 0.0
    return Quantity(float(v.mean()), math.hypot(sem, instrument_u))


def normalize_composition(comp: dict[str, float]) -> dict[str, float]:
    """Weight fractions summing to 1 (inputs may be fractions or percent; zeros dropped)."""
    c = {k: float(v) for k, v in comp.items() if float(v) > 0}
    for k in c:
        if k not in ELEMENTS:
            raise KeyError(f"bilinmeyen element sembolü: {k}")
    tot = sum(c.values())
    if tot <= 0:
        raise ValueError("bileşim boş")
    return {k: v / tot for k, v in c.items()}


def atoms_per_gram(comp_w: dict[str, float]) -> float:
    return N_A * sum(w / ELEMENTS[el][1] for el, w in comp_w.items())


# --------------------------------------------------------------------------- basic attenuation
def attenuation_exponent(rate0, u_rate0, rate, u_rate):
    """L = ln(R0/R) and its uncertainty from relative rate uncertainties (independent)."""
    L = math.log(rate0 / rate)
    return L, math.hypot(u_rate0 / rate0, u_rate / rate)


def lac(L: float, u_L: float, x_cm: float, u_x_cm: float):
    mu = L / x_cm
    return mu, math.hypot(u_L / x_cm, mu * u_x_cm / x_cm)


def mac(mu: float, u_mu: float, rho: float, u_rho: float):
    m = mu / rho
    return m, math.hypot(u_mu / rho, m * u_rho / rho)


def thickness_param(mu: float, u_mu: float, k: float):
    """HVL (k=ln2), TVL (k=ln10) or MFP (k=1):  k/mu.  NaN unless mu > 0."""
    if not (mu > 0):
        return float("nan"), float("nan")
    return k / mu, k / mu * u_mu / mu


def rpe(T: float, u_L: float):
    """Radiation protection efficiency in % and its uncertainty (T = I/I0 = exp(-L))."""
    return 100.0 * (1.0 - T), 100.0 * T * u_L


def significance(value: float, u: float) -> float:
    return abs(value) / u if u and u > 0 else float("inf")


# --------------------------------------------------------------------------- theory + Zeff
@dataclass
class TheoryPoint:
    energy_keV: float
    mu_rho: float          # cm^2/g, mixture rule
    sigma_a: float         # barn/atom
    sigma_e: float         # barn/electron
    zeff: float
    neff: float            # electrons/g
    n_atoms_per_g: float
    per_element: dict


def theory_point(xs: CrossSections, comp_w: dict[str, float], energy_keV: float) -> TheoryPoint:
    mu_rho_arr, per = mixture_mass_attenuation(xs, comp_w, [energy_keV])
    mu_rho = float(mu_rho_arr[0])
    n_g = atoms_per_gram(comp_w)
    f = {el: (w / ELEMENTS[el][1]) / (n_g / N_A) for el, w in comp_w.items()}       # atomic fractions
    sigma_e = sum(f[el] * ELEMENTS[el][1] / ELEMENTS[el][0] * float(per[el][0]) for el in comp_w) / N_A
    sigma_a = mu_rho / n_g
    return TheoryPoint(energy_keV, mu_rho, sigma_a / BARN, sigma_e / BARN, sigma_a / sigma_e,
                       mu_rho / sigma_e, n_g, {el: float(v[0]) for el, v in per.items()})


def experimental_zeff(mu_rho: float, u_mu_rho: float, th: TheoryPoint):
    """Direct-method Zeff, Neff from a measured MAC (sigma_e from tabulated elements)."""
    sigma_e = th.sigma_e * BARN
    zeff = mu_rho / (th.n_atoms_per_g * sigma_e)
    neff = mu_rho / sigma_e
    return (zeff, u_mu_rho / (th.n_atoms_per_g * sigma_e)), (neff, u_mu_rho / sigma_e)


# --------------------------------------------------------------------------- Monte-Carlo cross-check
def monte_carlo_lac(rate0, u0, rate, u, x, ux, rho, urho, n=200_000, seed=1):
    """Independent MC propagation (for validation of the analytic formulas)."""
    rng = np.random.default_rng(seed)
    r0 = rng.normal(rate0, u0, n)
    r = rng.normal(rate, u, n)
    xx = rng.normal(x, ux, n)
    rr = rng.normal(rho, urho, n)
    mu = np.log(r0 / r) / xx
    return {"mu": (mu.mean(), mu.std(ddof=1)), "mac": ((mu / rr).mean(), (mu / rr).std(ddof=1)),
            "hvl": (np.median(LN2 / mu), (LN2 / mu).std(ddof=1))}
