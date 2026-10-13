"""Synthetic NaI(Tl)-like spectra with *known* attenuation, used to validate the whole chain."""

from __future__ import annotations

import numpy as np
from scipy.special import erfc, ndtr

from gamma_shielding.lines import SOURCES
from gamma_shielding.spc import Spectrum

N_CH = 4096
CAL = (-0.5, 0.5016, 1.30e-5)           # true calibration
HEADER_CAL = (-4.6, 0.5208, 1.24e-5)    # deliberately off by 3 % like the real header

# line group -> (source, member energies, total area at T=1)
GROUPS = {
    "Ba-133 81": ("Ba-133", (79.6142, 80.9979), 31000.0),
    "Ba-133 303": ("Ba-133", (276.3989, 302.8508), 19000.0),
    "Ba-133 356": ("Ba-133", (356.0129, 383.8485), 50000.0),
    "Cs-137 662": ("Cs-137", (661.657,), 42000.0),
    "Co-60 1173": ("Co-60", (1173.228,), 146000.0),
    "Co-60 1332": ("Co-60", (1332.492,), 147000.0),
}


def energy(ch):
    return CAL[0] + CAL[1] * ch + CAL[2] * ch**2


def sigma_keV(E):
    return 19.8 * (E / 661.66) ** 0.672


def expected_spectrum(transmission: dict[str, float] | None = None) -> np.ndarray:
    """Mean counts per channel.  transmission[label] scales the full-energy peaks only."""
    transmission = transmission or {}
    ch = np.arange(N_CH, dtype=float)
    E = energy(ch)
    dEdch = CAL[1] + 2 * CAL[2] * ch
    y = 520.0 * np.exp(-E / 2500.0) + 150.0 + 0.0 * ch                      # smooth continuum
    # Compton plateaus ending at the Compton edges of the Co-60 lines (step down)
    for e0, h in ((1332.492, 260.0), (1173.228, 120.0)):
        edge = e0 - e0 / (1 + 2 * e0 / 510.999)
        y += h * 0.5 * erfc((E - edge) / (np.sqrt(2) * sigma_keV(edge)))
    y *= np.where(E > 1500, np.exp(-(E - 1500) / 60.0), 1.0)                # fall-off above the last line
    # lead-collimator features (not attenuated by the sample)
    for e0, a in ((47.0, 2500.0), (92.0, 8000.0)):
        s = 3.5 / np.interp(e0, E, dEdch)          # collimator features are narrower than the NaI law (as in real data)
        mu = np.interp(e0, E, ch)
        y += a * (ndtr((ch + 0.5 - mu) / s) - ndtr((ch - 0.5 - mu) / s))
    for label, (src, members, area) in GROUPS.items():
        w = {e: i for e, i in SOURCES[src]["lines"]}
        tot = sum(w[e] for e in members)
        t = transmission.get(label, 1.0)
        for e0 in members:
            s = sigma_keV(e0) / np.interp(e0, E, dEdch)
            mu = np.interp(e0, E, ch)
            y += area * t * w[e0] / tot * (ndtr((ch + 0.5 - mu) / s) - ndtr((ch - 0.5 - mu) / s))
    y[:3] = 0.0
    return y


def make_spectrum(name: str, transmission: dict[str, float] | None, seed: int, live: float = 7200.0) -> Spectrum:
    rng = np.random.default_rng(seed)
    counts = rng.poisson(expected_spectrum(transmission)).astype(np.int64)
    return Spectrum(name=name, counts=counts, live_time=live, real_time=live * 1.025,
                    header_calibration=HEADER_CAL)
