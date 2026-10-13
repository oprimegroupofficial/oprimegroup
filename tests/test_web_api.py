"""The browser entry points, exercised natively with synthetic .Spc files."""

import json
import math
import zipfile

import pytest

import synthetic as sy
from gamma_shielding import web_api
from gamma_shielding.composition import parse_composition
from gamma_shielding import physics as ph
from gamma_shielding.xsec import CrossSections
from spc_writer import spc_bytes

LINES = {"Ba-133 81": 80.8991, "Ba-133 303": 295.4176, "Ba-133 356": 359.5183, "Cs-137 662": 661.657,
         "Co-60 1173": 1173.228, "Co-60 1332": 1332.492}


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    data, out = tmp_path / "data", tmp_path / "out"
    data.mkdir()
    monkeypatch.setattr(web_api, "DATA_DIR", data)
    monkeypatch.setattr(web_api, "OUT_DIR", out)
    return data, out


def _write(data, name, spec):
    p = data / f"{name}.Spc"
    p.write_bytes(spc_bytes(spec.counts, spec.live_time, spec.real_time, name=name, cal=sy.HEADER_CAL))
    return str(p)


def test_parse_number_list():
    assert web_api.parse_number_list("2,01; 2.00  2,02") == [2.01, 2.0, 2.02]
    assert web_api.parse_number_list("6.3748, 6.3794, 6.3459") == [6.3748, 6.3794, 6.3459]
    assert web_api.parse_number_list("") == [] and web_api.parse_number_list(None) == []
    with pytest.raises(web_api.InputError):
        web_api.parse_number_list("2.0 abc")


def test_inspect_files(sandbox):
    data, _ = sandbox
    p1 = _write(data, "Dy2O3_05_5kaynak_2saat", sy.make_spectrum("a", None, 1))
    p2 = _write(data, "f7", sy.make_spectrum("b", None, 2))             # virtual path, original name passed separately
    bad = data / "bozuk.Spc"
    bad.write_bytes(b"x" * 100)
    rows = json.loads(web_api.inspect_files(json.dumps([p1, {"path": p2, "name": "Bos_5kaynak_2saat.Spc"}, str(bad)])))
    assert rows[0]["ok"] and rows[0]["role"] == "sample" and rows[0]["label"] == "Dy2O3_05"
    assert rows[1]["role"] == "blank" and rows[1]["live_time"] == pytest.approx(7200.0)
    assert not rows[2]["ok"] and "error" in rows[2]


def test_full_analysis_through_web_api(sandbox):
    data, out = sandbox
    xs = CrossSections()
    comp = parse_composition("Ni 0.7497; Al 0.1501; Bi 0.1002")
    rho, x_mm = 6.37, 2.0
    T = {k: math.exp(-ph.theory_point(xs, comp, E).mu_rho * rho * x_mm / 10) for k, E in LINES.items()}
    pb = _write(data, "Bos", sy.make_spectrum("b", None, 11))
    ps = _write(data, "Numune", sy.make_spectrum("s", T, 12))
    payload = {"project": "t", "settings": {"k": 2, "min_sig": 5, "variants": True},
               "files": [{"path": pb, "role": "blank", "name": "Bos"}, {"path": ps, "role": "sample", "name": "Dy-0"}],
               "samples": {ps: {"thickness": "2,00; 2.01; 1.99", "thickness_u_mm": 0.01, "density": "6,36; 6,37; 6,38",
                                "composition": "Ni 0.7497; Al 0.1501; Bi 0.1002", "composition_mode": "wt"}}}
    seen = []
    resp = json.loads(web_api.analyze(json.dumps(payload), progress=lambda m, f: seen.append((m, f))))
    assert resp["ok"], resp
    assert seen and seen[-1][1] <= 1.0 and any("Dy-0" in m for m, _ in seen)
    att = {r["Cizgi"]: r for r in resp["attenuation"]}
    r = att["Cs-137 662"]
    mu_true = ph.theory_point(xs, comp, 661.657).mu_rho * rho
    assert abs(r["LAC_cm-1"] - mu_true) < 4 * r["u_LAC_cm-1"]
    assert resp["has_blank"] and resp["summary"] and resp["plots"]
    assert resp["thickness_implied"]["Dy-0"][0] == pytest.approx(2.0, abs=0.5)
    with zipfile.ZipFile(out / "gama_zirhlama_sonuclar.zip") as z:
        names = z.namelist()
    assert "sonuclar.xlsx" in names and "rapor.md" in names and any(n.startswith("grafikler/") for n in names)


def test_errors_are_reported_not_raised(sandbox):
    data, _ = sandbox
    ps = _write(data, "Numune", sy.make_spectrum("s", None, 12))
    base = {"files": [{"path": ps, "role": "sample", "name": "A"}]}
    r = json.loads(web_api.analyze(json.dumps({**base, "samples": {ps: {"thickness": "abc"}}})))
    assert not r["ok"] and "sayı değil" in r["error"]
    r = json.loads(web_api.analyze(json.dumps({**base, "samples": {ps: {"composition": "Xx 5"}}})))
    assert not r["ok"] and "bileşim" in r["error"]
    r = json.loads(web_api.analyze(json.dumps({"files": [{"path": ps, "role": "ignore", "name": "A"}]})))
    assert not r["ok"] and "numune" in r["error"].lower()
    # no blank, no thickness: analysis still succeeds with warnings
    r = json.loads(web_api.analyze(json.dumps(base)))
    assert r["ok"] and not r["has_blank"] and r["warnings"]
