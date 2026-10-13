"""Photon mass attenuation coefficients of elements and mixtures.

Data: EPDL97 / Livermore evaluated photon data (the same family XCOM is built on), shipped as a
precomputed table (``data/elements_xs.npz``, made with ``tools/make_xs_table.py`` from ``fisx``).  Differences to NIST XCOM are typically below 1-2 % in the
0.05-2 MeV range.  If you need XCOM exactly, supply a CSV with columns
``element,energy_keV,mu_rho_cm2_g`` (elemental XCOM totals incl. coherent scattering);
it overrides the built-in values for the elements/energies it covers (log-log
interpolation).

Known issue worked around here: the pair-production column returned by fisx is wrong
between the 1022 keV threshold and ~1.25 MeV (e.g. 0.28 cm^2/g for Ni at 1050 keV).
Above the threshold but below 1300 keV the pair term is therefore replaced by the
near-threshold scaling pair(1300 keV) * ((E-1022)/(1300-1022))**3, which is
accurate to far better than the 0.1 % level it contributes to the total there.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

# Standard atomic weights (IUPAC, abridged) indexed by atomic number 1..92
_SYMBOLS = ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
            "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb "
            "Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U").split()
_WEIGHTS = (1.008, 4.0026, 6.94, 9.0122, 10.81, 12.011, 14.007, 15.999, 18.998, 20.180, 22.990, 24.305,
            26.982, 28.085, 30.974, 32.06, 35.45, 39.948, 39.098, 40.078, 44.956, 47.867, 50.942, 51.996,
            54.938, 55.845, 58.933, 58.693, 63.546, 65.38, 69.723, 72.630, 74.922, 78.971, 79.904, 83.798,
            85.468, 87.62, 88.906, 91.224, 92.906, 95.95, 98.0, 101.07, 102.91, 106.42, 107.87, 112.41,
            114.82, 118.71, 121.76, 127.60, 126.90, 131.29, 132.91, 137.33, 138.91, 140.12, 140.91, 144.24,
            145.0, 150.36, 151.96, 157.25, 158.93, 162.50, 164.93, 167.26, 168.93, 173.05, 174.97, 178.49,
            180.95, 183.84, 186.21, 190.23, 192.22, 195.08, 196.97, 200.59, 204.38, 207.2, 208.98, 209.0,
            210.0, 222.0, 223.0, 226.0, 227.0, 232.04, 231.04, 238.03)
ELEMENTS = {s: (z, a) for z, (s, a) in enumerate(zip(_SYMBOLS, _WEIGHTS), start=1)}

PAIR_THRESHOLD_KEV = 1021.998
PAIR_REF_KEV = 1300.0


def atomic_number(symbol: str) -> int:
    return ELEMENTS[symbol][0]


def atomic_weight(symbol: str) -> float:
    return ELEMENTS[symbol][1]


def _loglog(x, xs, ys):
    return np.exp(np.interp(np.log(x), np.log(xs), np.log(ys)))


TABLE_FILE = Path(__file__).parent / "data" / "elements_xs.npz"


class CrossSections:
    """Elemental photon cross sections in cm^2/g at arbitrary energies (keV).

    backend="table" (default when ``data/elements_xs.npz`` exists): precomputed EPDL97 totals,
    log-log interpolated - no extra dependency, also used by the browser version.
    backend="fisx": compute directly (needs ``pip install fisx``); gives the partial processes.
    """

    def __init__(self, override_csv: str | Path | None = None, backend: str = "auto"):
        if backend == "auto":
            backend = "table" if TABLE_FILE.exists() else "fisx"
        self.backend = backend
        self._override: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._pair_ref: dict[str, float] = {}
        if backend == "table":
            d = np.load(TABLE_FILE)
            self._grid = d["energies_keV"].astype(float)
            self._tab = d["total_cm2_g"].astype(float)
            self._row = {str(s): i for i, s in enumerate(d["symbols"])}
        elif backend == "fisx":
            try:
                import fisx
            except ImportError as exc:  # pragma: no cover
                raise ImportError("fisx paketi gerekli: pip install fisx") from exc
            self._el = fisx.Elements()
            self._el.initializeAsPyMca()
        else:
            raise ValueError(f"bilinmeyen backend: {backend}")
        if override_csv:
            self._load_override(Path(override_csv))

    def _load_override(self, path: Path):
        import pandas as pd
        df = pd.read_csv(path)
        cols = {c.lower().strip(): c for c in df.columns}
        for need in ("element", "energy_kev"):
            if need not in cols:
                raise ValueError(f"{path.name}: '{need}' sütunu yok (element, energy_keV, mu_rho_cm2_g)")
        ycol = next((cols[c] for c in ("mu_rho_cm2_g", "total", "mu_rho") if c in cols), None)
        if ycol is None:
            raise ValueError(f"{path.name}: 'mu_rho_cm2_g' sütunu yok")
        for el, g in df.groupby(cols["element"]):
            g = g.sort_values(cols["energy_kev"])
            self._override[str(el)] = (g[cols["energy_kev"]].to_numpy(float), g[ycol].to_numpy(float))

    def components(self, symbol: str, energy_keV) -> dict[str, np.ndarray]:
        """Partial processes (fisx backend only)."""
        if self.backend != "fisx":
            raise RuntimeError("components() için backend='fisx' gerekir")
        e = np.atleast_1d(np.asarray(energy_keV, dtype=float))
        if symbol not in ELEMENTS:
            raise KeyError(f"bilinmeyen element: {symbol}")
        r = self._el.getMassAttenuationCoefficients(symbol, e.tolist())
        coh, inc, pho = (np.asarray(r[k], dtype=float) for k in ("coherent", "compton", "photoelectric"))
        pair = np.asarray(r["pair"], dtype=float).copy()
        mid = (e > PAIR_THRESHOLD_KEV) & (e < PAIR_REF_KEV)
        if mid.any():
            if symbol not in self._pair_ref:
                self._pair_ref[symbol] = float(self._el.getMassAttenuationCoefficients(symbol, [PAIR_REF_KEV])["pair"][0])
            frac = (e[mid] - PAIR_THRESHOLD_KEV) / (PAIR_REF_KEV - PAIR_THRESHOLD_KEV)
            pair[mid] = self._pair_ref[symbol] * frac**3
        pair[e <= PAIR_THRESHOLD_KEV] = 0.0
        return {"coherent": coh, "incoherent": inc, "photoelectric": pho, "pair": pair,
                "total": coh + inc + pho + pair}

    def total(self, symbol: str, energy_keV):
        """Total mass attenuation coefficient (with coherent scattering), cm^2/g."""
        e = np.atleast_1d(np.asarray(energy_keV, dtype=float))
        if symbol not in ELEMENTS:
            raise KeyError(f"bilinmeyen element: {symbol}")
        if symbol in self._override:
            xs, ys = self._override[symbol]
            if e.min() >= xs.min() and e.max() <= xs.max():
                return _loglog(e, xs, ys)
        if self.backend == "table":
            if e.min() < self._grid[0] or e.max() > self._grid[-1]:
                raise ValueError(f"enerji tablo aralığının dışında ({self._grid[0]:.0f}-{self._grid[-1]:.0f} keV)")
            return _loglog(e, self._grid, self._tab[self._row[symbol]])
        return self.components(symbol, e)["total"]


def mixture_mass_attenuation(xs: CrossSections, weight_fractions: dict[str, float], energy_keV):
    """mu/rho of a mixture by the mixture rule, plus the elemental values used."""
    e = np.atleast_1d(np.asarray(energy_keV, dtype=float))
    per = {el: xs.total(el, e) for el in weight_fractions}
    mu = sum(w * per[el] for el, w in weight_fractions.items())
    return mu, per
