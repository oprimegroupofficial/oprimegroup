"""Per-spectrum analysis: calibration, peak fits, resolution refinement and model variants."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

import numpy as np

from .calibration import Calibration, find_anchors, fit_calibration
from .lines import ANCHORS, default_regions, default_variants
from .peakfit import RegionFit, RegionSpec, Resolution, fit_region
from .spc import Spectrum

MIN_SIGNIFICANCE_DEFAULT = 5.0


@dataclass
class LineMeas:
    key: str
    region: str
    source: str
    E_main: float
    E_eff: float
    area: float
    u_stat: float                    # incl. Birge scaling
    rate: float                      # counts per live second
    u_rate_stat: float
    live_time: float
    chi2_red: float
    ndf: int
    fit_ok: bool
    message: str
    E_fit_keV: float
    fwhm_keV: float
    variant_areas: dict = field(default_factory=dict)   # variant id -> area (accepted variants only)
    rejected_variants: dict = field(default_factory=dict)  # variant id -> reason

    @property
    def significance(self) -> float:
        return abs(self.area) / self.u_stat if self.u_stat and np.isfinite(self.u_stat) and self.u_stat > 0 else 0.0

    @property
    def fwhm_percent(self) -> float:
        return 100.0 * self.fwhm_keV / self.E_fit_keV if self.E_fit_keV else float("nan")


@dataclass
class SpectrumAnalysis:
    spectrum: Spectrum
    calibration: Calibration
    initial_calibration: Calibration
    resolution: Resolution
    fits: dict = field(default_factory=dict)            # region -> {"base": RegionFit, "variants": {vid: RegionFit}}
    lines: dict = field(default_factory=dict)           # label -> LineMeas
    warnings: list = field(default_factory=list)


def _variant_id(v: dict) -> str:
    parts = []
    if "region" in v:
        r: RegionSpec = v["region"]
        steps = "+".join(p.label for p in r.peaks if p.step)
        parts.append(f"yapi[step:{steps or '-'},bkg{r.bkg_order},tie{int(r.tie_sigma)},edge{len(r.compton_edges_keV)}]")
    if "bkg_order" in v:
        parts.append(f"bkg{v['bkg_order']}")
    if "window_scale" in v:
        parts.append(f"pencere x{v['window_scale']:.2f}")
    return " ".join(parts)


def calibrate(spec: Spectrum, anchors=None, order: int | None = None, tol: float = 0.08,
              manual_coeffs=None) -> Calibration:
    n = spec.n_channels
    if manual_coeffs is not None:
        return Calibration(np.asarray(manual_coeffs, float), n_channels=n, source="manual")
    anchors = anchors or ANCHORS
    found = find_anchors(spec.counts, anchors, spec.header_energy, tol=tol)
    if len(found) < 2:
        raise RuntimeError(
            f"{spec.name}: enerji kalibrasyonu için yeterli çapa tepe bulunamadı ({len(found)}). "
            "Yapılandırmada kalibrasyon katsayılarını elle verin.")
    ord_ = order or (2 if len(found) >= 4 else 1)
    cal = fit_calibration(found, order=ord_, n_channels=n)
    # reject gross outliers (> 2.5 % of E) once
    bad = [a for a in cal.anchors if abs(a["residual_keV"]) > 0.025 * a["E_keV"]]
    if bad and len(found) - len(bad) >= 2:
        keep = [f for f in found if f["label"] not in {b["label"] for b in bad}]
        cal = fit_calibration(keep, order=order or (2 if len(keep) >= 4 else 1), n_channels=n)
    return cal


def _accept_variant(base: RegionFit, v: RegionFit) -> str | None:
    if not v.ok:
        return "uydurma başarısız"
    if not np.isfinite(v.chi2_red) or v.chi2_red > max(1.5, 1.3 * base.chi2_red):
        return f"kötü uyum (chi2/ndf={v.chi2_red:.2f})"
    return None


def _line_from_fits(label: str, region: str, source: str, base: RegionFit, variants: dict, cal: Calibration,
                    live_time: float) -> LineMeas:
    pk = base.peaks[label]
    area = pk["area"]
    u = pk["u_area"]
    var_areas, rejected = {}, {}
    for vid, vf in variants.items():
        why = _accept_variant(base, vf)
        if why is None and label in vf.peaks:
            a = vf.peaks[label]["area"]
            ua = vf.peaks[label]["u_area"]
            if np.isfinite(ua) and ua > 0 and np.isfinite(a):
                var_areas[vid] = a
            else:
                rejected[vid] = "belirsizlik hesaplanamadı"
        elif why is not None:
            rejected[vid] = why
    mu = pk["mu_ch"]
    fwhm = 2.3548 * pk["sigma_ch"] * float(cal.dE_dch(mu))
    return LineMeas(key=label, region=region, source=source, E_main=pk["E_main"], E_eff=pk["E_eff"],
                    area=area, u_stat=u, rate=area / live_time, u_rate_stat=u / live_time,
                    live_time=live_time, chi2_red=base.chi2_red, ndf=base.ndf, fit_ok=base.ok,
                    message=base.message, E_fit_keV=float(cal.energy(mu)), fwhm_keV=fwhm,
                    variant_areas=var_areas, rejected_variants=rejected)


def analyze_spectrum(spec: Spectrum, regions: list[RegionSpec] | None = None, *, anchors=None,
                     calibration_order: int | None = None, manual_coeffs=None, with_variants: bool = True,
                     variants_fn=default_variants, peak_sources: dict | None = None) -> SpectrumAnalysis:
    regions = regions or default_regions()
    cal0 = calibrate(spec, anchors, calibration_order, manual_coeffs=manual_coeffs)
    res = Resolution()
    warnings: list[str] = []
    counts = spec.counts

    def peak_energies_sigmas(fits, cal):
        e, s = [], []
        for f in fits:
            if not f.ok:
                continue
            for pk in f.peaks.values():
                if pk["reported"] and np.isfinite(pk["u_area"]) and pk["u_area"] > 0 and abs(pk["area"]) / pk["u_area"] >= 15:
                    e.append(pk["E_main"])
                    s.append(pk["sigma_ch"] * float(cal.dE_dch(pk["mu_ch"])))
        return e, s

    # pass 1 with the default resolution, then refine the resolution law from the data
    fits1 = [fit_region(counts, cal0, r, res) for r in regions]
    e, s = peak_energies_sigmas(fits1, cal0)
    res = Resolution.from_points(e, s, default=res)

    out = SpectrumAnalysis(spec, cal0, cal0, res)
    pts = []
    for r in regions:
        base = fit_region(counts, cal0, r, res)
        variants: dict[str, RegionFit] = {}
        if with_variants:
            for v in variants_fn(r):
                vr = v.get("region", r)
                vf = fit_region(counts, cal0, vr, res, window_scale=v.get("window_scale", 1.0),
                                bkg_order=v.get("bkg_order"))
                variants[_variant_id(v)] = vf
        out.fits[r.name] = {"base": base, "variants": variants}
        for p in r.peaks:
            if p.reported:
                out.lines[p.label] = _line_from_fits(p.label, r.name, p.source, base, variants, cal0, spec.live_time)
                pk = base.peaks[p.label]
                if base.ok and np.isfinite(pk["u_area"]) and pk["u_area"] > 0 and abs(pk["area"]) / pk["u_area"] >= 20:
                    pts.append({"label": p.label, "E_keV": p.E_main, "ch": pk["mu_ch"], "u_ch": max(pk["u_mu_ch"], 0.05)})
        if not base.ok:
            warnings.append(f"{spec.name}: '{r.name}' bölgesi uydurulamadı ({base.message}).")
        elif base.chi2_red > 1.6:
            warnings.append(f"{spec.name}: '{r.name}' uyumu zayıf (chi2/ndf={base.chi2_red:.2f}); belirsizlik Birge katsayısı ile büyütüldü.")

    # final calibration from fitted centroids (reporting; fits above used the anchor calibration)
    if len(pts) >= 3:
        try:
            out.calibration = fit_calibration(pts, order=calibration_order or (2 if len(pts) >= 4 else 1),
                                              n_channels=spec.n_channels, source="fit (tepe merkezleri)")
        except ValueError:
            out.calibration = cal0
    out.warnings = warnings
    return out
