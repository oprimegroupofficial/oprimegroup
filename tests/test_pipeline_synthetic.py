"""End-to-end validation: spectra with known attenuation must give the right LAC with honest errors."""

import math

import numpy as np
import pytest

import synthetic as sy
from gamma_shielding.config import Config, SampleCfg
from gamma_shielding.pipeline import BLANK_NAME, run
from gamma_shielding.xsec import CrossSections

MU_TRUE = {"Ba-133 81": 2.2, "Ba-133 303": 0.9, "Ba-133 356": 0.75, "Cs-137 662": 0.50,
           "Co-60 1173": 0.36, "Co-60 1332": 0.34}
X_MM = 5.0


def _cfg(tmp_path, thickness=True):
    s = SampleCfg(name="S", file="-", thickness_mm=[X_MM - 0.01, X_MM, X_MM + 0.01] if thickness else None,
                  thickness_u_mm=0.01, density=[6.30, 6.31, 6.29],
                  composition={"Ni": 0.75, "Al": 0.15, "Bi": 0.10})
    return Config(project="t", root=tmp_path, spectra_dir=tmp_path, out_dir=tmp_path / "out", samples=[s])


@pytest.fixture(scope="module")
def xs():
    return CrossSections()


def _one(tmp_path, xs, seed, thickness=True):
    T = {k: math.exp(-m * X_MM / 10.0) for k, m in MU_TRUE.items()}
    T["Am-65"] = 0.004
    spectra = {"S": sy.make_spectrum("S", T, seed), BLANK_NAME: sy.make_spectrum("blank", None, seed + 10_000)}
    return run(_cfg(tmp_path, thickness), xs, spectra=spectra)


def test_recovers_known_lac_single_replicate(tmp_path, xs):
    res = _one(tmp_path, xs, 1)
    df = res.attenuation.set_index("Cizgi")
    assert set(MU_TRUE) <= set(df.index)
    for line, mu in MU_TRUE.items():
        r = df.loc[line]
        assert abs(r["LAC_cm-1"] - mu) < 4.5 * r["u_LAC_cm-1"], (line, r["LAC_cm-1"], mu, r["u_LAC_cm-1"])
        assert r["u_LAC_cm-1"] > 0
    # derived quantities are consistent with LAC
    r = df.loc["Cs-137 662"]
    assert r["HVL_cm"] == pytest.approx(math.log(2) / r["LAC_cm-1"])
    assert r["MAC_cm2_g"] == pytest.approx(r["LAC_cm-1"] / r["rho_g_cm3"])
    assert r["RPE_yuzde"] == pytest.approx(100 * (1 - r["T_I_I0"]))
    assert 5 < r["Zeff"] < 80 and r["Neff_e_g"] > 1e23


def test_without_blank_or_thickness_degrades_gracefully(tmp_path, xs):
    res = run(_cfg(tmp_path), xs, spectra={"S": sy.make_spectrum("S", None, 3)})
    assert res.attenuation.empty and not res.peaks.empty
    assert any("Numunesiz" in w for w in res.warnings)
    res2 = _one(tmp_path, xs, 2, thickness=False)
    assert "LAC_cm-1" not in res2.attenuation.columns
    assert res2.attenuation["Not"].str.contains("kalınlık yok").all()


def test_undetected_line_is_dropped(tmp_path, xs):
    res = _one(tmp_path, xs, 5)
    assert not any(k.startswith("Co-57") for k in res.attenuation["Cizgi"])
    assert any("Co-57" in w and "tespit edilemeyen" in w for w in res.warnings)


def test_excess_counts_with_sample_are_flagged_not_converted_to_negative_lac(tmp_path, xs):
    """A line that is *larger* with the sample (e.g. fluorescence) must not give a negative LAC / Zeff."""
    T = {k: math.exp(-m * X_MM / 10.0) for k, m in MU_TRUE.items()}
    T["Ba-133 356"] = 1.35
    T["Am-65"] = 0.004
    spectra = {"S": sy.make_spectrum("S", T, 21), BLANK_NAME: sy.make_spectrum("b", None, 22)}
    res = run(_cfg(tmp_path), xs, spectra=spectra)
    r = res.attenuation.set_index("Cizgi").loc["Ba-133 356"]
    assert "I > I0" in r["Not"]
    assert ("LAC_cm-1" not in r.index) or math.isnan(r["LAC_cm-1"])
    ok = res.attenuation.set_index("Cizgi").loc["Cs-137 662"]
    assert ok["LAC_cm-1"] > 0


def test_blank_scale_factor_and_diagnostic(tmp_path, xs):
    """Sample runs 7 % 'brighter' than the blank: the diagnostic finds k and an independently measured k removes the bias."""
    from gamma_shielding import physics as ph
    from gamma_shielding.composition import parse_composition
    comp = parse_composition("Ni 0.75; Al 0.15; Bi 0.10")
    rho, x_mm, k_true = 6.30, 3.3, 1.07
    E = {"Ba-133 303": 295.4176, "Ba-133 356": 359.5183, "Cs-137 662": 661.657, "Co-60 1173": 1173.228, "Co-60 1332": 1332.492}
    T = {k: k_true * math.exp(-ph.theory_point(xs, comp, e).mu_rho * rho * x_mm / 10) for k, e in E.items()}
    T["Am-65"] = 0.004
    T["Ba-133 81"] = 0.95
    spectra = {"S": sy.make_spectrum("S", T, 31), BLANK_NAME: sy.make_spectrum("b", None, 32)}
    cfg = _cfg(tmp_path)
    cfg.samples[0].thickness_mm = [x_mm]
    cfg.samples[0].density = [rho]
    res = run(cfg, xs, spectra=spectra)
    d = res.status["scale_diagnostic"]["S"]
    assert d["k"] == pytest.approx(k_true, abs=0.04) and d["chi2"] / d["ndf"] < 3
    assert any("Tanı" in w for w in res.warnings)
    mu_th = ph.theory_point(xs, comp, 1332.492).mu_rho * rho
    cfg2 = _cfg(tmp_path)
    cfg2.samples[0].thickness_mm = [x_mm]
    cfg2.samples[0].density = [rho]
    cfg2.blank_scale, cfg2.blank_scale_u = k_true, 0.005
    res2 = run(cfg2, xs, spectra=spectra)
    r = res2.attenuation.set_index("Cizgi").loc["Co-60 1332"]
    assert abs(r["LAC_cm-1"] - mu_th) < 3 * r["u_LAC_cm-1"]
    r1 = res.attenuation.set_index("Cizgi").loc["Co-60 1332"]
    assert abs(r1["LAC_cm-1"] - mu_th) > 3 * r1["u_LAC_cm-1"]           # uncorrected: clearly biased low


@pytest.mark.slow
def test_pull_distribution_is_unit_normal(tmp_path, xs):
    pulls = {k: [] for k in MU_TRUE}
    n_rep = 14
    for seed in range(n_rep):
        df = _one(tmp_path, xs, 100 + seed).attenuation.set_index("Cizgi")
        for line, mu in MU_TRUE.items():
            r = df.loc[line]
            pulls[line].append((r["LAC_cm-1"] - mu) / r["u_LAC_cm-1"])
    allp = np.concatenate([np.array(v) for v in pulls.values()])
    print({k: (round(float(np.mean(v)), 2), round(float(np.std(v, ddof=1)), 2)) for k, v in pulls.items()})
    print("all:", allp.mean(), allp.std(ddof=1))
    assert abs(allp.mean()) < 0.4            # no net bias
    assert 0.6 < allp.std(ddof=1) < 1.5      # errors neither badly over- nor under-estimated
    assert np.mean(np.abs(allp) < 2.0) > 0.85


def test_implied_thickness_matches_truth_when_theory_is_consistent(tmp_path, xs):
    """Data generated with the *tabulated* mu of the sample => implied thickness == real thickness."""
    from gamma_shielding import physics as ph
    comp = ph.normalize_composition({"Ni": 0.75, "Al": 0.15, "Bi": 0.10})
    rho, x_cm = 6.30, 0.05
    lines = {"Ba-133 81": 80.8991, "Ba-133 303": 295.4176, "Ba-133 356": 359.5183, "Cs-137 662": 661.657, "Co-60 1173": 1173.228, "Co-60 1332": 1332.492}
    T = {k: math.exp(-ph.theory_point(xs, comp, E).mu_rho * rho * x_cm) for k, E in lines.items()}
    cfg = _cfg(tmp_path)
    spectra = {"S": sy.make_spectrum("S", T, 7), BLANK_NAME: sy.make_spectrum("b", None, 8)}
    res = run(cfg, xs, spectra=spectra)
    xi, uxi = res.status["thickness_implied"]["S"]
    # _cfg declares a measured thickness of 5 mm, the data imply 0.5 mm -> must be flagged
    assert xi == pytest.approx(0.5, abs=max(3 * uxi, 0.05))
    assert any("uyuşmuyor" in w for w in res.warnings)     # measured 5 mm vs implied 0.5 mm must be flagged
