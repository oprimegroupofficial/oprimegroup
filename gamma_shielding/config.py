"""YAML configuration loading and validation (user-facing keys are Turkish, ASCII only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import yaml

from .lines import ANCHORS, default_regions
from .peakfit import PeakSpec, RegionSpec


class ConfigError(ValueError):
    pass


@dataclass
class SampleCfg:
    name: str
    file: str
    thickness_mm: list[float] | None = None
    thickness_u_mm: float = 0.01          # standard uncertainty of the thickness instrument/non-uniformity
    density: list[float] | None = None    # measured, g/cm3 (repeats allowed)
    density_u: float = 0.0                # extra standard uncertainty (g/cm3)
    theoretical_density: float | None = None
    composition: dict[str, float] | None = None
    start: datetime | None = None


@dataclass
class Config:
    project: str
    root: Path
    spectra_dir: Path
    out_dir: Path
    samples: list[SampleCfg]
    blank_file: str | None = None
    blank_start: datetime | None = None
    blank_scale: float = 1.0              # I0 rate multiplier (independently measured geometry/flux correction)
    blank_scale_u: float = 0.0            # its standard uncertainty (relative, e.g. 0.01 = 1 %)
    coverage_k: float = 1.0
    min_significance: float = 5.0
    decay_correction: bool = False
    use_header_time: bool = False
    calibration_order: int | None = None
    calibration_coeffs: list[float] | None = None
    exclude_lines: list[str] = field(default_factory=list)
    regions: list[RegionSpec] | None = None
    anchors: list = field(default_factory=lambda: list(ANCHORS))
    xs_csv: str | None = None
    xs_rel_uncertainty: float = 0.0       # relative standard uncertainty of tabulated cross sections
    variants: bool = True


def _as_list(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return [float(v)]
    v = [float(x) for x in v if x is not None]
    return v or None


def _dt(v):
    if v in (None, "", "null"):
        return None
    if isinstance(v, datetime):
        return v
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(str(v), fmt)
        except ValueError:
            pass
    raise ConfigError(f"tarih/saat okunamadı: {v!r} (örnek: 2026-10-13 08:00)")


def _regions_from_cfg(items) -> list[RegionSpec]:
    out = []
    for r in items:
        peaks = []
        for p in r["tepeler"]:
            peaks.append(PeakSpec(
                label=p["ad"], energies=tuple(float(e) for e in p["enerjiler"]),
                weights=tuple(float(w) for w in p.get("agirliklar", [1.0] * len(p["enerjiler"]))),
                reported=bool(p.get("raporlanan", True)), free_E_keV=p.get("serbest_E_keV"),
                source=p.get("kaynak", ""), step=bool(p.get("adim", False))))
        out.append(RegionSpec(
            name=r["ad"], lo_keV=float(r["alt_keV"]), hi_keV=float(r["ust_keV"]), peaks=tuple(peaks),
            bkg_order=int(r.get("bkg_derece", 1)),
            compton_edges_keV=tuple(float(e) for e in r.get("compton_kenar_keV", [])),
            tie_sigma=bool(r.get("sigma_bagla", False))))
    return out


def load_config(path: str | Path) -> Config:
    path = Path(path).resolve()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path.name} YAML hatası: {exc}") from exc
    base = Path(raw.get("temel_klasor", "."))          # all other paths are relative to this folder
    root = (path.parent / base).resolve() if not base.is_absolute() else base
    return build_config(raw, root)


def build_config(raw: dict, root: Path) -> Config:
    """Config from the (Turkish-key) dictionary used in the YAML file; also used by the web version."""

    def res(p):
        p = Path(p)
        return p if p.is_absolute() else (root / p)

    if not raw.get("numuneler"):
        raise ConfigError("'numuneler' listesi boş")
    samples = []
    for s in raw["numuneler"]:
        for key in ("ad", "dosya"):
            if key not in s:
                raise ConfigError(f"numune tanımı '{key}' içermiyor: {s}")
        comp = s.get("bilesim_agirlik")
        samples.append(SampleCfg(
            name=str(s["ad"]), file=str(s["dosya"]), thickness_mm=_as_list(s.get("kalinlik_mm")),
            thickness_u_mm=float(s.get("kalinlik_belirsizlik_mm", 0.01)),
            density=_as_list(s.get("yogunluk_g_cm3")), density_u=float(s.get("yogunluk_ek_belirsizlik", 0.0)),
            theoretical_density=s.get("kuramsal_yogunluk_g_cm3"),
            composition={str(k): float(v) for k, v in comp.items()} if comp else None,
            start=_dt(s.get("baslangic"))))
    names = [s.name for s in samples]
    if len(set(names)) != len(names):
        raise ConfigError("numune adları benzersiz olmalı")

    blank = raw.get("bos_olcum") or {}
    cal = raw.get("kalibrasyon") or {}
    return Config(
        project=str(raw.get("proje", "gama zirhlama analizi")),
        root=root,
        spectra_dir=res(raw.get("spektrum_klasoru", "data/raw")),
        out_dir=res(raw.get("cikti_klasoru", "output")),
        samples=samples,
        blank_file=blank.get("dosya"),
        blank_start=_dt(blank.get("baslangic")),
        blank_scale=float(blank.get("olcek_carpani") or 1.0), blank_scale_u=float(blank.get("olcek_belirsizligi") or 0.0),
        coverage_k=float(raw.get("kapsam_katsayisi", 1.0)),
        min_significance=float(raw.get("min_anlamlilik", 5.0)),
        decay_correction=bool((raw.get("bozunma_duzeltmesi") or {}).get("etkin", False)),
        use_header_time=bool((raw.get("bozunma_duzeltmesi") or {}).get("baslik_zamani_kullan", False)),
        calibration_order=cal.get("derece"), calibration_coeffs=cal.get("katsayilar"),
        exclude_lines=list(raw.get("cizgiler_haric", []) or []),
        regions=_regions_from_cfg(raw["bolgeler"]) if raw.get("bolgeler") else None,
        xs_csv=str(res(raw["xcom_csv"])) if raw.get("xcom_csv") else None,
        xs_rel_uncertainty=float(raw.get("tesir_kesiti_goreli_belirsizlik", 0.0)),
        variants=bool(raw.get("model_varyantlari", True)))
