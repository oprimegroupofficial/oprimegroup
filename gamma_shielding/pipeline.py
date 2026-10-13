"""End-to-end pipeline: spectra -> net peak areas -> I0/I -> LAC and shielding parameters."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from . import physics as ph
from .analysis import LineMeas, SpectrumAnalysis, analyze_spectrum
from .config import Config, SampleCfg
from .lines import SOURCES, default_regions
from .spc import Spectrum, read_spc
from .xsec import CrossSections

REFERENCE_MATERIALS = {
    "Kursun (Pb)": ({"Pb": 1.0}, 11.35),
    "Siradan beton (NIST)": ({"H": 0.0221, "C": 0.002484, "O": 0.57493, "Na": 0.015208, "Mg": 0.001266,
                              "Al": 0.019953, "Si": 0.304627, "K": 0.010045, "Ca": 0.042951, "Fe": 0.006435}, 2.30),
}


@dataclass
class Results:
    cfg: Config
    spectra: dict = field(default_factory=dict)          # name -> Spectrum
    analyses: dict = field(default_factory=dict)         # name -> SpectrumAnalysis
    blank_name: str | None = None
    peaks: pd.DataFrame = field(default_factory=pd.DataFrame)
    relative: pd.DataFrame = field(default_factory=pd.DataFrame)
    attenuation: pd.DataFrame = field(default_factory=pd.DataFrame)
    theory: pd.DataFrame = field(default_factory=pd.DataFrame)
    reference: pd.DataFrame = field(default_factory=pd.DataFrame)
    samples_info: pd.DataFrame = field(default_factory=pd.DataFrame)
    calibration: pd.DataFrame = field(default_factory=pd.DataFrame)
    warnings: list = field(default_factory=list)
    status: dict = field(default_factory=dict)


# ------------------------------------------------------------------------------ helpers
def _find_spc(cfg: Config, fname: str) -> Path:
    p = Path(fname)
    cand = [p] if p.is_absolute() else [cfg.spectra_dir / p, cfg.root / p]
    for c in cand:
        if c.exists():
            return c
    low = {q.name.lower(): q for q in cfg.spectra_dir.glob("*") if q.is_file()} if cfg.spectra_dir.exists() else {}
    if p.name.lower() in low:
        return low[p.name.lower()]
    raise FileNotFoundError(f"spektrum dosyasi bulunamadi: {fname} (aranan klasor: {cfg.spectra_dir})")


def _mid_time(spec: Spectrum, start):
    t0 = start or spec.start
    return None if t0 is None else t0 + timedelta(seconds=spec.real_time / 2)


def decay_factor(source: str, dt_days: float) -> float:
    """Factor by which a count rate measured dt_days *after* the reference is reduced."""
    hl = SOURCES[source]["half_life_d"]
    return math.exp(-math.log(2.0) * dt_days / hl)


def model_spread(lnR_base: float, lnR_variants: list[float]) -> float:
    """Model-dependence uncertainty of ln(I0/I): sample std over {baseline} + accepted variants."""
    v = np.array([lnR_base] + list(lnR_variants), dtype=float)
    v = v[np.isfinite(v)]
    if v.size >= 3:
        return float(np.std(v, ddof=1))
    if v.size == 2:
        return float(abs(v[0] - v[1]) / 2.0)
    return 0.0


def _ratio(l0: LineMeas, l1: LineMeas, decay: float = 1.0):
    """ln(R0/R1) with statistical and model uncertainty; decay = factor reducing R1 (corrected R1 = R1/decay)."""
    R0, R1 = l0.rate, l1.rate / decay
    L = math.log(R0 / R1)
    u_stat = math.hypot(l0.u_stat / abs(l0.area), l1.u_stat / abs(l1.area))
    common = [v for v in l0.variant_areas if v in l1.variant_areas]
    lv = []
    for v in common:
        a0, a1 = l0.variant_areas[v], l1.variant_areas[v]
        if a0 > 0 and a1 > 0:
            lv.append(math.log((a0 / l0.live_time) / (a1 / l1.live_time / decay)))
    return L, u_stat, model_spread(L, lv), len(lv)


# ------------------------------------------------------------------------------ main steps
BLANK_NAME = "Bos (I0)"


def load_spectra(cfg: Config, res: Results) -> dict[str, Spectrum]:
    spectra = {s.name: read_spc(_find_spc(cfg, s.file)) for s in cfg.samples}
    if cfg.blank_file:
        try:
            spectra[BLANK_NAME] = read_spc(_find_spc(cfg, cfg.blank_file))
        except FileNotFoundError as exc:
            res.warnings.append(f"Numunesiz (bos) olcum bulunamadi: {exc}. LAC hesaplanamaz; yalnizca pik tablosu uretildi.")
    return spectra


def analyze_all(cfg: Config, res: Results, spectra: dict[str, Spectrum]):
    regions = cfg.regions or default_regions()
    res.blank_name = BLANK_NAME if BLANK_NAME in spectra else None
    for name, spec in spectra.items():
        res.spectra[name] = spec
        a = analyze_spectrum(spec, regions, anchors=cfg.anchors, calibration_order=cfg.calibration_order,
                             manual_coeffs=cfg.calibration_coeffs, with_variants=cfg.variants)
        for key in cfg.exclude_lines:
            a.lines.pop(key, None)
        res.analyses[name] = a
        res.warnings += a.warnings
        if spec.dead_time_fraction > 0.30:
            res.warnings.append(f"{name}: olu zaman %{100*spec.dead_time_fraction:.0f}; sayim hizi yuksek, olu zaman duzeltmesi guvenilir olmayabilir.")


def detected_lines(cfg: Config, res: Results) -> dict[str, float]:
    """Lines (label -> effective energy) found significantly in at least one spectrum."""
    out = {}
    for a in res.analyses.values():
        for key, L in a.lines.items():
            if L.fit_ok and L.area > 0 and L.significance >= cfg.min_significance:
                out[key] = L.E_eff
    return out


def build_tables(cfg: Config, res: Results):
    rows, cal_rows = [], []
    for name, a in res.analyses.items():
        spec = a.spectrum
        for key, L in a.lines.items():
            va = np.array(list(L.variant_areas.values()), dtype=float)
            spread = (float(np.std(np.append(va, L.area), ddof=1)) / abs(L.area)
                      if va.size >= 2 and L.area else float("nan"))
            rows.append({
                "Spektrum": name, "Cizgi": key, "Kaynak": L.source, "E_nominal_keV": L.E_eff,
                "E_uydurma_keV": L.E_fit_keV, "FWHM_keV": L.fwhm_keV, "FWHM_yuzde": L.fwhm_percent,
                "Net_alan": L.area, "u_alan_ist": L.u_stat, "Anlamlilik_sigma": L.significance,
                "Hiz_cps": L.rate, "u_hiz_ist_cps": L.u_rate_stat, "chi2_ndf": L.chi2_red, "ndf": L.ndf,
                "Kabul_varyant": len(L.variant_areas), "Red_varyant": len(L.rejected_variants),
                "Alan_model_dagilimi_yuzde": 100 * spread, "Canli_sure_s": spec.live_time,
                "Gercek_sure_s": spec.real_time, "Tespit": "evet" if (L.fit_ok and L.significance >= cfg.min_significance and L.area > 0) else "hayir",
                "Uydurma_notu": L.message})
        cal = a.calibration
        cal_rows.append({"Spektrum": name, "Kalibrasyon": cal.describe(), "RMS_artik_keV": cal.rms_residual_keV,
                         "Kaynak": cal.source, "Cozunurluk_FWHM_662_yuzde": float(a.resolution.fwhm_percent(661.66)),
                         "Cozunurluk_ussu": a.resolution.p, "Toplam_sayim": spec.total_counts,
                         "Canli_sure_s": spec.live_time, "Gercek_sure_s": spec.real_time,
                         "Olu_zaman_yuzde": 100 * spec.dead_time_fraction,
                         "Sayim_hizi_cps": spec.total_counts / spec.live_time,
                         "Baslik_zamani": str(spec.start) if spec.start else "", "Aciklama": spec.description})
    res.peaks = pd.DataFrame(rows)
    res.calibration = pd.DataFrame(cal_rows)


def relative_table(cfg: Config, res: Results):
    """Attenuation of every sample relative to a reference spectrum (blank if present, else first sample)."""
    ref = res.blank_name or cfg.samples[0].name
    a0 = res.analyses[ref]
    rows = []
    for s in cfg.samples:
        if s.name == ref:
            continue
        a1 = res.analyses[s.name]
        for key, l0 in a0.lines.items():
            l1 = a1.lines.get(key)
            if l1 is None or min(l0.significance, l1.significance) < cfg.min_significance or l0.area <= 0 or l1.area <= 0:
                continue
            L, us, um, nv = _ratio(l0, l1)
            u = math.hypot(us, um)
            rows.append({"Referans": ref, "Numune": s.name, "Cizgi": key, "E_keV": l0.E_eff,
                         "T=I/Iref": math.exp(-L), "u_T": math.exp(-L) * u, "ln(Iref/I)": L, "u_ist": us,
                         "u_model": um, "u_toplam": u, "Anlamlilik_sigma": abs(L) / u, "Model_varyant_sayisi": nv})
    res.relative = pd.DataFrame(rows)
    res.status["relative_reference"] = ref
    if not res.relative.empty and not res.blank_name:
        big = res.relative.groupby("Numune")["Anlamlilik_sigma"].max()
        if (big < 3.0).all():
            res.warnings.append(
                f"'{ref}' referansina gore hicbir numunede hicbir cizgide 3 sigma'yi asan fark yok: spektrumlar "
                "istatistiksel olarak ayirt edilemiyor. Numunenin isin yolunda oldugundan ve kalinligin yeterli "
                "oldugundan emin olun (numunesiz olcumle karsilastirinca netlesir).")


def theory_tables(cfg: Config, res: Results, xs: CrossSections):
    energies = detected_lines(cfg, res)
    rows, info = [], []
    for s in cfg.samples:
        rho = ph.mean_with_sem(s.density, s.density_u) if s.density else ph.Quantity(float("nan"), float("nan"))
        T = ph.mean_with_sem(s.thickness_mm, s.thickness_u_mm) if s.thickness_mm else ph.Quantity(float("nan"), float("nan"))
        info.append({"Numune": s.name, "Dosya": s.file, "Kalinlik_mm": T.value, "u_kalinlik_mm": T.u,
                     "Kalinlik_olcum_sayisi": len(s.thickness_mm or []), "Yogunluk_g_cm3": rho.value,
                     "u_yogunluk_g_cm3": rho.u, "Yogunluk_olcum_sayisi": len(s.density or []),
                     "Kuramsal_yogunluk_g_cm3": s.theoretical_density,
                     "Bosluk_yuzde": (100 * (1 - rho.value / s.theoretical_density)
                                      if s.theoretical_density and s.density else float("nan")),
                     "Bilesim": ", ".join(f"{k} {100 * v:.2f}%" for k, v in
                                          ph.normalize_composition(s.composition).items()) if s.composition else ""})
        if not s.composition:
            continue
        comp = ph.normalize_composition(s.composition)
        wsum = sum(v for v in s.composition.values())
        if abs(wsum - 1.0) > 0.01 and abs(wsum - 100.0) > 1.0:
            res.warnings.append(f"{s.name}: bilesim agirlik kesirlerinin toplami {wsum:.4f}; 1'e normalize edildi.")
        for key, E in sorted(energies.items(), key=lambda kv: kv[1]):
            tp = ph.theory_point(xs, comp, E)
            r = {"Numune": s.name, "Cizgi": key, "E_keV": E, "MAC_kuram_cm2_g": tp.mu_rho,
                 "sigma_a_barn": tp.sigma_a, "sigma_e_barn": tp.sigma_e, "Zeff_kuram": tp.zeff,
                 "Neff_kuram_e_g": tp.neff}
            if np.isfinite(rho.value):
                mu_t = tp.mu_rho * rho.value
                r.update({"LAC_kuram_cm-1": mu_t, "HVL_kuram_cm": ph.LN2 / mu_t, "TVL_kuram_cm": ph.LN10 / mu_t,
                          "MFP_kuram_cm": 1 / mu_t, "Ne_kuram_e_cm3": tp.neff * rho.value})
            rows.append(r)
    res.theory = pd.DataFrame(rows)
    res.samples_info = pd.DataFrame(info)
    ref_rows = []
    for mat, (comp, rho) in REFERENCE_MATERIALS.items():
        for key, E in sorted(energies.items(), key=lambda kv: kv[1]):
            mu_rho = float(ph.mixture_mass_attenuation(xs, comp, [E])[0][0])
            ref_rows.append({"Malzeme": mat, "Yogunluk_g_cm3": rho, "Cizgi": key, "E_keV": E,
                             "MAC_cm2_g": mu_rho, "LAC_cm-1": mu_rho * rho, "HVL_cm": ph.LN2 / (mu_rho * rho)})
    res.reference = pd.DataFrame(ref_rows)


def attenuation_table(cfg: Config, res: Results, xs: CrossSections):
    if not res.blank_name:
        return
    a0 = res.analyses[res.blank_name]
    detected = {k for k, L in a0.lines.items() if L.fit_ok and L.area > 0 and L.significance >= cfg.min_significance}
    rows = []
    for s in cfg.samples:
        a1 = res.analyses[s.name]
        rho = ph.mean_with_sem(s.density, s.density_u) if s.density else None
        thick = ph.mean_with_sem(s.thickness_mm, s.thickness_u_mm) if s.thickness_mm else None
        comp = ph.normalize_composition(s.composition) if s.composition else None
        t_blank = _mid_time(res.spectra[res.blank_name], cfg.blank_start if not cfg.use_header_time else None)
        t_samp = _mid_time(res.spectra[s.name], s.start if not cfg.use_header_time else None)
        for key, l0 in a0.lines.items():
            l1 = a1.lines.get(key)
            if l1 is None or key not in detected:
                continue
            row = {"Numune": s.name, "Cizgi": key, "Kaynak": l0.source, "E_keV": l0.E_eff}
            flags = []
            if min(l0.significance, l1.significance) < cfg.min_significance or l0.area <= 0 or l1.area <= 0:
                row["Not"] = (f"tespit edilemedi (I0: {l0.significance:.1f} sigma, I: {l1.significance:.1f} sigma)")
                rows.append(row)
                continue
            decay = 1.0
            if cfg.decay_correction and t_blank and t_samp and l0.source in SOURCES:
                decay = decay_factor(l0.source, (t_samp - t_blank).total_seconds() / 86400.0)
            elif cfg.decay_correction:
                flags.append("bozunma duzeltmesi icin zaman bilgisi yok")
            L, u_st, u_mod, nv = _ratio(l0, l1, decay)
            u_L = math.hypot(u_st, u_mod)
            T = math.exp(-L)
            row.update({"I0_cps": l0.rate, "u_I0_cps": l0.u_rate_stat, "I_cps": l1.rate / decay, "u_I_cps": l1.u_rate_stat / decay,
                        "T_I_I0": T, "u_T": T * u_L, "L_ln_I0_I": L, "u_L_ist": u_st, "u_L_model": u_mod, "u_L": u_L,
                        "Model_varyant_sayisi": nv, "Bozunma_duzeltme_carpani": decay})
            rpe_v, u_rpe = ph.rpe(T, u_L)
            row.update({"RPE_yuzde": rpe_v, "u_RPE_yuzde": u_rpe, "L_anlamlilik_sigma": abs(L) / u_L if u_L else float("inf")})
            if comp and rho:
                # consistency check: thickness implied by the data and the tabulated mu
                mu_th = ph.theory_point(xs, comp, l0.E_eff).mu_rho * rho.value
                row.update({"LAC_kuram_cm-1": mu_th, "Kalinlik_cikarsanan_mm": 10.0 * L / mu_th,
                            "u_Kalinlik_cikarsanan_mm": 10.0 * u_L / mu_th})
            if thick:
                x, ux = thick.value / 10.0, thick.u / 10.0
                mu, umu = ph.lac(L, u_L, x, ux)
                row.update({"x_cm": x, "u_x_cm": ux, "LAC_cm-1": mu, "u_LAC_cm-1": umu,
                            "LAC_anlamlilik_sigma": abs(mu) / umu if umu else float("inf"),
                            "Katki_ist_I0": (l0.u_stat / abs(l0.area) / x), "Katki_ist_I": (l1.u_stat / abs(l1.area) / x),
                            "Katki_model": u_mod / x, "Katki_kalinlik": abs(mu) * ux / x})
                for nm, k in (("HVL", ph.LN2), ("TVL", ph.LN10), ("MFP", 1.0)):
                    v, u = ph.thickness_param(mu, umu, k)
                    row[f"{nm}_cm"], row[f"u_{nm}_cm"] = v, u
                if mu <= 0 or abs(mu) / umu < 3:
                    flags.append("LAC < 3 sigma: HVL/TVL/MFP guvenilir degil" if mu > 0 else "LAC <= 0: I >= I0")
                if rho:
                    m, um_ = ph.mac(mu, umu, rho.value, rho.u)
                    row.update({"rho_g_cm3": rho.value, "u_rho_g_cm3": rho.u, "MAC_cm2_g": m, "u_MAC_cm2_g": um_})
                    if comp:
                        tp = ph.theory_point(xs, comp, l0.E_eff)
                        (z, uz), (n, un) = ph.experimental_zeff(m, um_, tp)
                        row.update({"Zeff": z, "u_Zeff": uz, "Neff_e_g": n, "u_Neff_e_g": un,
                                    "Ne_e_cm3": n * rho.value, "u_Ne_e_cm3": math.hypot(un * rho.value, n * rho.u),
                                    "sigma_a_barn": m / tp.n_atoms_per_g / ph.BARN,
                                    "u_sigma_a_barn": um_ / tp.n_atoms_per_g / ph.BARN,
                                    "sigma_e_barn": tp.sigma_e})
                        mu_t_rho = tp.mu_rho
                        urel = cfg.xs_rel_uncertainty
                        mu_t = mu_t_rho * rho.value
                        row.update({"MAC_kuram_cm2_g": mu_t_rho, "LAC_kuram_cm-1": mu_t,
                                    "HVL_kuram_cm": ph.LN2 / mu_t, "Zeff_kuram": tp.zeff, "Neff_kuram_e_g": tp.neff,
                                    "Sapma_MAC_yuzde": 100 * (m - mu_t_rho) / mu_t_rho,
                                    "u_Sapma_MAC_yuzde": 100 * math.hypot(um_ / mu_t_rho, m * urel / mu_t_rho)})
                else:
                    flags.append("yogunluk yok: MAC/Zeff/Neff hesaplanamadi")
            else:
                flags.append("kalinlik yok: LAC/MAC/HVL/TVL/MFP/Zeff hesaplanamadi")
            if flags:
                row["Not"] = "; ".join(flags)
            rows.append(row)
    res.attenuation = pd.DataFrame(rows)
    df = res.attenuation
    if not df.empty and "Kalinlik_cikarsanan_mm" in df.columns:
        for sc in cfg.samples:
            g = df[(df["Numune"] == sc.name)].dropna(subset=["Kalinlik_cikarsanan_mm"])
            if g.empty:
                continue
            w = 1.0 / g["u_Kalinlik_cikarsanan_mm"] ** 2
            xi = float((g["Kalinlik_cikarsanan_mm"] * w).sum() / w.sum())
            uxi = float(1.0 / np.sqrt(w.sum()))
            res.status.setdefault("thickness_implied", {})[sc.name] = (xi, uxi)
            if sc.thickness_mm:
                xm = ph.mean_with_sem(sc.thickness_mm, sc.thickness_u_mm)
                if abs(xi - xm.value) > 3 * math.hypot(uxi, xm.u):
                    res.warnings.append(
                        f"{sc.name}: verilerden cikarsanan kalinlik {xi:.3g} ± {uxi:.2g} mm, olculen {xm.value:.3g} mm ile "
                        "uyusmuyor (>3 sigma): geometri, numune konumu veya kalinlik degerini kontrol edin.")
    if not df.empty and "L_anlamlilik_sigma" in df.columns:
        for name, g in df.groupby("Numune"):
            sig = g["L_anlamlilik_sigma"].dropna()
            if len(sig) and (sig < 3.0).all():
                res.warnings.append(
                    f"{name}: numunesiz olcume gore hicbir cizgide 3 sigma'yi asan zayiflama yok; "
                    "numune isin yolunda mi / kalinlik yeterli mi kontrol edin. Hesaplanan LAC degerleri belirsiz.")


def run(cfg: Config, xs: CrossSections | None = None, spectra: dict[str, Spectrum] | None = None) -> Results:
    """Run the whole analysis.  ``spectra`` (name -> Spectrum, blank under BLANK_NAME) bypasses file reading."""
    res = Results(cfg)
    analyze_all(cfg, res, spectra if spectra is not None else load_spectra(cfg, res))
    build_tables(cfg, res)
    relative_table(cfg, res)
    xs = xs or CrossSections(cfg.xs_csv)
    theory_tables(cfg, res, xs)
    attenuation_table(cfg, res, xs)
    nd = {}
    for a in res.analyses.values():
        for key, L in a.lines.items():
            nd[key] = max(nd.get(key, 0.0), L.significance if L.fit_ok else 0.0)
    missing = [f"{k} (en yuksek {v:.1f} sigma)" for k, v in nd.items() if v < cfg.min_significance]
    if missing:
        res.warnings.append("Spektrumlarda tespit edilemeyen cizgiler (analiz disi birakildi): " + "; ".join(missing))
    res.status.update({
        "blank": bool(res.blank_name),
        "thickness_all": all(s.thickness_mm for s in cfg.samples),
        "density_all": all(s.density for s in cfg.samples),
        "composition_all": all(s.composition for s in cfg.samples)})
    if not res.status["blank"]:
        res.warnings.append("Numunesiz (I0) spektrum tanimli degil: LAC/MAC/HVL/TVL/MFP/RPE/Zeff/Neff hesaplanmadi.")
    elif not res.status["thickness_all"]:
        miss = [s.name for s in cfg.samples if not s.thickness_mm]
        res.warnings.append("Kalinlik girilmemis numuneler: " + ", ".join(miss) + " (LAC icin 'kalinlik_mm' gerekli).")
    return res
