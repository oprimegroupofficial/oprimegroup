"""Builds a clearly labelled SYNTHETIC example output (not real data) showing the final deliverable layout.

    python examples/make_synthetic_example.py
"""

import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

import synthetic as sy  # noqa: E402

from gamma_shielding import physics as ph  # noqa: E402
from gamma_shielding.config import Config, SampleCfg  # noqa: E402
from gamma_shielding.pipeline import BLANK_NAME, run  # noqa: E402
from gamma_shielding.report import write_all  # noqa: E402
from gamma_shielding.xsec import CrossSections  # noqa: E402

LINES = {"Ba-133 81": 80.8991, "Ba-133 303": 295.4176, "Ba-133 356": 359.5183, "Cs-137 662": 661.657,
         "Co-60 1173": 1173.228, "Co-60 1332": 1332.492}
SAMPLES = [  # name, weight fractions, density, thickness mm  (invented for the example)
    ("ORNEK-A", {"Ni": 0.7497, "Al": 0.1501, "Bi": 0.1002}, 6.37, 2.00),
    ("ORNEK-B", {"Ni": 0.5498, "Al": 0.1501, "Bi": 0.1002, "Dy": 0.1742, "O": 0.0257}, 6.28, 2.00),
]


def main():
    xs = CrossSections()
    out = ROOT / "examples" / "sentetik_ornek"
    spectra = {BLANK_NAME: sy.make_spectrum("bos", None, 1)}
    samples = []
    for i, (name, comp, rho, x_mm) in enumerate(SAMPLES):
        c = ph.normalize_composition(comp)
        # "true" LAC = tabulated value x 1.03 (so the experiment-vs-theory column is not trivially zero)
        T = {k: math.exp(-1.03 * ph.theory_point(xs, c, E).mu_rho * rho * x_mm / 10) for k, E in LINES.items()}
        spectra[name] = sy.make_spectrum(name, T, 10 + i)
        samples.append(SampleCfg(name=name, file="-", thickness_mm=[x_mm - 0.01, x_mm, x_mm + 0.01], thickness_u_mm=0.01,
                                 density=[rho - 0.01, rho, rho + 0.01], composition=comp,
                                 theoretical_density=rho * 1.04))
    cfg = Config(project="SENTETIK ORNEK - GERCEK VERI DEGILDIR (yalnizca cikti bicimini gostermek icin)", root=ROOT,
                 spectra_dir=ROOT, out_dir=out, samples=samples, coverage_k=2.0)
    res = run(cfg, xs, spectra=spectra)
    write_all(res, xs)
    print("yazildi:", out)


if __name__ == "__main__":
    main()
