import math

import numpy as np
import pytest

from gamma_shielding import physics as ph
from gamma_shielding.xsec import CrossSections


@pytest.fixture(scope="module")
def xs():
    return CrossSections()


def test_analytic_propagation_matches_monte_carlo():
    r0, u0, r, u, x, ux, rho, urho = 4.2, 0.03, 3.1, 0.03, 0.52, 0.004, 6.3, 0.02
    L, uL = ph.attenuation_exponent(r0, u0, r, u)
    mu, umu = ph.lac(L, uL, x, ux)
    m, um = ph.mac(mu, umu, rho, urho)
    hvl, uhvl = ph.thickness_param(mu, umu, ph.LN2)
    mc = ph.monte_carlo_lac(r0, u0, r, u, x, ux, rho, urho)
    assert mc["mu"][1] == pytest.approx(umu, rel=0.02)
    assert mc["mac"][1] == pytest.approx(um, rel=0.02)
    assert mc["hvl"][1] == pytest.approx(uhvl, rel=0.05)
    assert mu == pytest.approx(math.log(r0 / r) / x)


def test_hvl_tvl_mfp_relations():
    hvl, _ = ph.thickness_param(0.5, 0.01, ph.LN2)
    tvl, _ = ph.thickness_param(0.5, 0.01, ph.LN10)
    mfp, umfp = ph.thickness_param(0.5, 0.01, 1.0)
    assert hvl == pytest.approx(math.log(2) / 0.5)
    assert tvl / hvl == pytest.approx(math.log(10) / math.log(2))
    assert mfp == pytest.approx(2.0) and umfp == pytest.approx(0.04)
    assert all(math.isnan(v) for v in ph.thickness_param(-0.1, 0.05, ph.LN2))


def test_rpe_limits():
    v, u = ph.rpe(1.0, 0.02)
    assert v == 0.0 and u == pytest.approx(2.0)
    v, _ = ph.rpe(math.exp(-math.log(2)), 0.0)
    assert v == pytest.approx(50.0)


def test_mean_with_sem():
    q = ph.mean_with_sem([6.3748, 6.3794, 6.3459])
    assert q.value == pytest.approx(6.3667, abs=1e-4)
    assert q.u == pytest.approx(np.std([6.3748, 6.3794, 6.3459], ddof=1) / math.sqrt(3))
    q2 = ph.mean_with_sem([2.0], instrument_u=0.01)
    assert q2.value == 2.0 and q2.u == 0.01
    q3 = ph.mean_with_sem([2.0, 2.0, 2.0], instrument_u=0.01)
    assert q3.u == pytest.approx(0.01)


def test_composition_normalisation_and_errors():
    c = ph.normalize_composition({"Ni": 0.7, "Al": 0.15, "Bi": 0.1, "Dy": 0.0})
    assert sum(c.values()) == pytest.approx(1.0) and "Dy" not in c
    with pytest.raises(KeyError):
        ph.normalize_composition({"Xx": 1.0})


@pytest.mark.parametrize("el,Z", [("Pb", 82), ("Ni", 28), ("Al", 13)])
def test_zeff_of_pure_element_is_its_Z(xs, el, Z):
    for E in (81.0, 356.0, 661.66, 1332.5):
        tp = ph.theory_point(xs, {el: 1.0}, E)
        assert tp.zeff == pytest.approx(Z, rel=1e-9)


def test_zeff_water_and_neff(xs):
    w = {"H": 0.111894, "O": 0.888106}
    tp = ph.theory_point(xs, w, 661.66)
    assert tp.mu_rho == pytest.approx(0.0857, rel=0.015)       # NIST XCOM water, 662 keV
    # direct method (Manohara et al.) is atom-weighted in the Compton region: (2*1 + 8)/3
    assert tp.zeff == pytest.approx(10.0 / 3.0, rel=0.02)
    # Neff = N_A Z_eff / <A>
    n_expected = ph.N_A * tp.zeff / (1.0 / sum(f / ph.ELEMENTS[e][1] for e, f in w.items()))
    assert tp.neff == pytest.approx(n_expected, rel=1e-9)


def test_experimental_zeff_roundtrip(xs):
    comp = {"Ni": 0.75, "Al": 0.15, "Bi": 0.10}
    tp = ph.theory_point(xs, comp, 356.0)
    (z, uz), (n, un) = ph.experimental_zeff(tp.mu_rho, 0.01 * tp.mu_rho, tp)
    assert z == pytest.approx(tp.zeff) and n == pytest.approx(tp.neff)
    assert uz / z == pytest.approx(0.01) and un / n == pytest.approx(0.01)


def test_composition_parser():
    from gamma_shielding.composition import CompositionError, parse_composition, parse_formula
    c = parse_composition("Ni 0,7497; Al 0.1501, Bi 0.1002")
    assert c["Ni"] == pytest.approx(0.7497, abs=1e-4) and sum(c.values()) == pytest.approx(1.0)
    d = parse_composition("Dy2O3 5")                     # 5 wt% Dy2O3 -> Dy 0.8713 of it
    assert d["Dy"] == pytest.approx(0.8713, abs=2e-4)
    m = parse_composition("SiO2 50; B2O3 50", mode="mol")
    assert m["Si"] / m["B"] == pytest.approx(ph.ELEMENTS["Si"][1] / (2 * ph.ELEMENTS["B"][1]), rel=1e-9)
    assert parse_formula("Ca(OH)2") == {"Ca": 1.0, "O": 2.0, "H": 2.0}
    for bad in ("", "Xx 5", "Ni", "Ni 0.5; Q 1", "Ca(OH 3"):
        with pytest.raises(CompositionError):
            parse_composition(bad)
