"""Regenerates gamma_shielding/data/elements_xs.npz (needs ``pip install fisx``).

The table holds the total mass attenuation coefficient (with coherent scattering, cm^2/g) of
elements Z=1..92 on a log-spaced energy grid; it lets the package (and the browser version)
run without fisx.  Source: EPDL97 through fisx, pair production corrected near threshold
(see gamma_shielding/xsec.py).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gamma_shielding.xsec import _SYMBOLS, CrossSections  # noqa: E402

E_MIN, E_MAX, N = 10.0, 6000.0, 4000


def main():
    xs = CrossSections(backend="fisx")
    grid = np.geomspace(E_MIN, E_MAX, N)
    table = np.empty((len(_SYMBOLS), N), dtype=np.float32)
    for i, sym in enumerate(_SYMBOLS):
        table[i] = xs.components(sym, grid)["total"]
    out = ROOT / "gamma_shielding" / "data" / "elements_xs.npz"
    out.parent.mkdir(exist_ok=True)
    np.savez_compressed(out, energies_keV=grid, total_cm2_g=table, symbols=np.array(_SYMBOLS),
                        description=np.array("EPDL97 (fisx 1.3.x) total mass attenuation coefficient incl. coherent, "
                                             "pair production corrected near threshold; cm^2/g"))
    print(out, out.stat().st_size / 1e6, "MB")


if __name__ == "__main__":
    main()
