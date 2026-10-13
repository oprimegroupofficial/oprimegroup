"""Nuclide data and default analysis regions for the Am-241 / Ba-133 / Co-57 / Cs-137 / Co-60 set.

Gamma energies and emission probabilities: DDEP / NNDC evaluated data (rounded);
half-lives: DDEP.  Edit ``SOURCES`` or override regions in the YAML configuration
when a different source set is used.
"""

from __future__ import annotations

from dataclasses import replace

from .peakfit import PeakSpec, RegionSpec

DAY = 1.0
YEAR = 365.25

# name -> half-life [days], gamma lines [(E_keV, I_percent)]
SOURCES: dict[str, dict] = {
    "Am-241": {"half_life_d": 432.6 * YEAR, "lines": [(59.5409, 35.92)]},
    "Ba-133": {"half_life_d": 10.551 * YEAR,
               "lines": [(79.6142, 2.62), (80.9979, 34.06), (276.3989, 7.164),
                         (302.8508, 18.33), (356.0129, 62.05), (383.8485, 8.94)]},
    "Co-57": {"half_life_d": 271.74 * DAY, "lines": [(122.0614, 85.60), (136.4743, 10.68)]},
    "Cs-137": {"half_life_d": 30.08 * YEAR, "lines": [(661.657, 84.99)]},
    "Co-60": {"half_life_d": 5.2713 * YEAR, "lines": [(1173.228, 99.85), (1332.492, 99.98)]},
}

# Calibration anchors: (label, effective energy keV).  Effective energy of an unresolved
# multiplet is the intensity weighted mean (Ba-133 356+384 -> 359.5 keV).
ANCHORS = [("Ba-133 81", 81.0), ("Ba-133 303", 302.85), ("Ba-133 356", 359.5),
           ("Cs-137 662", 661.66), ("Co-60 1173", 1173.23), ("Co-60 1332", 1332.49)]


def _group(label, source, lines_E, **kw):
    comps = [(e, i) for e, i in SOURCES[source]["lines"] if any(abs(e - x) < 1e-6 for x in lines_E)]
    return PeakSpec(label=label, energies=tuple(c[0] for c in comps), weights=tuple(c[1] for c in comps),
                    source=source, **kw)


def default_regions() -> list[RegionSpec]:
    """Baseline regions.  ``variants`` (below) give the model-dependence systematics."""
    pb210 = PeakSpec("Pb-210 46.5 (kolimatör)", (47.0,), (1.0,), reported=False, free_E_keV=5.0)
    pb_kx = PeakSpec("Pb K-X / 92 keV omuz", (92.0,), (1.0,), reported=False, free_E_keV=8.0)
    return [
        RegionSpec("Am-241 59.5", 36, 68,
                   (pb210, _group("Am-241 59.5", "Am-241", (59.5409,), free_E_keV=2.5)), bkg_order=1),
        RegionSpec("Ba-133 81", 62, 118,
                   (_group("Ba-133 81", "Ba-133", (79.6142, 80.9979)), pb_kx), bkg_order=1),
        RegionSpec("Co-57 122", 104, 200,
                   (_group("Co-57 122", "Co-57", (122.0614, 136.4743), free_E_keV=4.0),), bkg_order=2),
        RegionSpec("Ba-133 303/356", 245, 450,
                   (_group("Ba-133 303", "Ba-133", (276.3989, 302.8508)),
                    _group("Ba-133 356", "Ba-133", (356.0129, 383.8485))), bkg_order=2),
        RegionSpec("Cs-137 662", 540, 800,
                   (_group("Cs-137 662", "Cs-137", (661.657,)),), bkg_order=2),
        RegionSpec("Co-60 1173/1332", 1000, 1460,
                   (_group("Co-60 1173", "Co-60", (1173.228,)),
                    _group("Co-60 1332", "Co-60", (1332.492,))),
                   bkg_order=1, compton_edges_keV=(1332.492,), tie_sigma=True),
    ]


def _stepped(region: RegionSpec, labels: tuple[str, ...] | None = None) -> RegionSpec:
    peaks = tuple(replace(p, step=True) if (p.reported and (labels is None or p.label in labels)) else p
                  for p in region.peaks)
    return replace(region, peaks=peaks)


def default_variants(region: RegionSpec) -> list[dict]:
    """Alternative, equally plausible analysis choices for a region.

    Each variant is a dict of overrides: ``bkg_order``, ``window_scale`` and/or
    ``region`` (a replacement RegionSpec).  The spread of ln(I0/I) over the variants
    that still fit the data is used as the model-dependence uncertainty.
    """
    base = region.bkg_order
    v = [
        {"bkg_order": base + 1},
        {"window_scale": 0.85},
        {"window_scale": 1.15},
        {"window_scale": 0.85, "bkg_order": base + 1},
        {"window_scale": 1.15, "bkg_order": base + 1},
    ]
    if region.name in ("Ba-133 81", "Ba-133 303/356", "Cs-137 662"):
        v.append({"region": replace(_stepped(region), bkg_order=1)})
        v.append({"region": _stepped(region)})
    if region.name == "Co-60 1173/1332":
        stepped = replace(_stepped(region), tie_sigma=False)
        v.append({"region": stepped})
        v.append({"region": replace(stepped, bkg_order=2)})
        v.append({"region": replace(region, tie_sigma=False)})
    return v
