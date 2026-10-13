"""Entry points for the browser version (Pyodide).  JavaScript writes the uploaded files into the
virtual file system (/data) and calls :func:`inspect_files` / :func:`analyze` with JSON strings."""

from __future__ import annotations

import json
import re
import shutil
import traceback
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from .composition import CompositionError, parse_composition
from .config import ConfigError, build_config
from .pipeline import run
from .report import _budget_table, _summary_table, write_all
from .spc import SpcFormatError, parse_spc
from .xsec import CrossSections

DATA_DIR = Path("/data")
OUT_DIR = Path("/out")
BLANK_HINT = re.compile(r"(^|[^a-z])(bos|blank|numunesiz|empty|nosample|no_sample|i0)([^a-z]|$)", re.I)


class InputError(ValueError):
    pass


def parse_number_list(text, what: str = "deger") -> list[float]:
    """'2.01; 2.00 2,02' -> [2.01, 2.0, 2.02] (decimal comma allowed between digits)."""
    if text is None:
        return []
    if isinstance(text, (int, float)):
        return [float(text)]
    t = re.sub(r"(?<=\d),(?=\d)", ".", str(text))
    out = []
    for tok in re.split(r"[;\s,]+", t.strip()):
        if not tok:
            continue
        try:
            out.append(float(tok))
        except ValueError as exc:
            raise InputError(f"{what}: '{tok}' sayı değil. Okumaları boşluk veya ';' ile ayırın.") from exc
    return out


def _json(df: pd.DataFrame | None):
    if df is None or df.empty:
        return []
    return json.loads(df.replace([np.inf, -np.inf], np.nan).to_json(orient="records", force_ascii=False))


def inspect_files(items_json: str) -> str:
    """items: list of paths or of {path, name} (name = original file name shown to the user)."""
    out = []
    for it in json.loads(items_json):
        p, orig = (it["path"], it.get("name")) if isinstance(it, dict) else (it, None)
        path = Path(p)
        shown = Path(orig) if orig else path
        row = {"path": str(path), "file": shown.name, "ok": False}
        try:
            s = parse_spc(path.read_bytes(), shown.stem, str(path))
            row.update({"ok": True, "name": s.name, "channels": s.n_channels, "counts": s.total_counts,
                        "live_time": s.live_time, "real_time": s.real_time,
                        "dead_pct": 100 * s.dead_time_fraction, "start": str(s.start) if s.start else "",
                        "role": "blank" if BLANK_HINT.search(shown.stem) else "sample",
                        "label": re.sub(r"_?5?kaynak.*$", "", shown.stem, flags=re.I) or shown.stem})
        except (SpcFormatError, OSError) as exc:
            row["error"] = str(exc)
        out.append(row)
    return json.dumps(out, ensure_ascii=False)


def _build(payload: dict):
    files = [f for f in payload["files"] if f.get("role") in ("sample", "blank")]
    blanks = [f for f in files if f["role"] == "blank"]
    samples = [f for f in files if f["role"] == "sample"]
    if not samples:
        raise InputError("En az bir numune spektrumu seçin (rol: Numune).")
    if len(blanks) > 1:
        raise InputError("Yalnızca bir numunesiz (I0) spektrum seçilebilir.")
    st = payload.get("settings", {})
    meta = payload.get("samples", {})
    names = [f["name"].strip() or Path(f["path"]).stem for f in samples]
    if len(set(names)) != len(names):
        raise InputError("Numune adları benzersiz olmalı.")
    raw_samples = []
    for f, name in zip(samples, names):
        m = meta.get(f["path"], meta.get(name, {}))
        comp = None
        if str(m.get("composition", "")).strip():
            try:
                comp = parse_composition(m["composition"], m.get("composition_mode", "wt"))
            except CompositionError as exc:
                raise InputError(f"{name}: bileşim: {exc}") from exc
        theo = parse_number_list(m.get("theo_density"), f"{name}: kuramsal yoğunluk")
        raw_samples.append({
            "ad": name, "dosya": f["path"],
            "kalinlik_mm": parse_number_list(m.get("thickness"), f"{name}: kalınlık") or None,
            "kalinlik_belirsizlik_mm": float(m.get("thickness_u_mm") or 0.01),
            "yogunluk_g_cm3": parse_number_list(m.get("density"), f"{name}: yoğunluk") or None,
            "kuramsal_yogunluk_g_cm3": theo[0] if theo else None,
            "bilesim_agirlik": comp})
    raw = {
        "proje": payload.get("project") or "Gama zirhlama analizi",
        "spektrum_klasoru": str(DATA_DIR), "cikti_klasoru": str(OUT_DIR),
        "bos_olcum": {"dosya": blanks[0]["path"] if blanks else None,
                      "olcek_carpani": float(st.get("blank_scale") or 1.0),
                      "olcek_belirsizligi": float(st.get("blank_scale_u") or 0.0)},
        "kapsam_katsayisi": float(st.get("k", 1)), "min_anlamlilik": float(st.get("min_sig", 5)),
        "model_varyantlari": bool(st.get("variants", True)),
        "cizgiler_haric": list(st.get("exclude_lines", [])),
        "tesir_kesiti_goreli_belirsizlik": float(st.get("xs_rel_unc", 0.0)),
        "xcom_csv": st.get("xcom_csv") or None,
        "numuneler": raw_samples}
    return build_config(raw, DATA_DIR)


def analyze(payload_json: str, progress=None) -> str:
    try:
        payload = json.loads(payload_json)
        cfg = _build(payload)
        if OUT_DIR.exists():
            shutil.rmtree(OUT_DIR)
        OUT_DIR.mkdir(parents=True)
        xs = CrossSections(cfg.xs_csv)
        res = run(cfg, xs, progress=progress)
        write_all(res, xs, progress=progress)
        zpath = OUT_DIR / "gama_zirhlama_sonuclar.zip"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(OUT_DIR.rglob("*")):
                if f.is_file() and f != zpath:
                    z.write(f, f.relative_to(OUT_DIR).as_posix())
        files = [{"path": str(f), "name": f.relative_to(OUT_DIR).as_posix(), "size": f.stat().st_size}
                 for f in sorted(OUT_DIR.rglob("*")) if f.is_file()]
        att = res.attenuation
        resp = {
            "ok": True, "status": {k: v for k, v in res.status.items() if k != "thickness_implied"},
            "thickness_implied": {k: list(v) for k, v in res.status.get("thickness_implied", {}).items()},
            "warnings": res.warnings, "coverage_k": cfg.coverage_k,
            "summary": _json(_summary_table(res)), "attenuation": _json(att), "peaks": _json(res.peaks),
            "relative": _json(res.relative), "theory": _json(res.theory), "reference": _json(res.reference),
            "calibration": _json(res.calibration), "samples_info": _json(res.samples_info),
            "budget": _json(_budget_table(res)), "files": files,
            "plots": [f["name"] for f in files if f["name"].endswith(".png")],
            "has_blank": bool(res.blank_name),
            "lines": sorted({k for a in res.analyses.values() for k in a.lines})}
        return json.dumps(resp, ensure_ascii=False)
    except (InputError, ConfigError, FileNotFoundError, RuntimeError, SpcFormatError, ValueError) as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
    except Exception as exc:  # pragma: no cover - surfaced to the user with details
        return json.dumps({"ok": False, "error": f"Beklenmeyen hata: {exc}", "detail": traceback.format_exc()},
                          ensure_ascii=False)


def available_lines() -> str:
    from .lines import default_regions
    return json.dumps([p.label for r in default_regions() for p in r.peaks if p.reported])


def parse_comp(text: str, mode: str = "wt") -> str:
    """Live validation of the composition box: returns JSON {ok, fractions | error}."""
    try:
        f = parse_composition(text, mode)
        return json.dumps({"ok": True, "fractions": f}, ensure_ascii=False)
    except (CompositionError, ValueError) as exc:
        return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
