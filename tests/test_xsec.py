import numpy as np
import pytest

from gamma_shielding.xsec import CrossSections, atomic_weight


@pytest.fixture(scope="module")
def xs():
    return CrossSections()                      # precomputed table (default)


@pytest.fixture(scope="module")
def xs_fisx():
    pytest.importorskip("fisx")
    return CrossSections(backend="fisx")


# NIST XCOM / NISTIR 5632 values (cm2/g, total with coherent)
@pytest.mark.parametrize("sym,E,ref,tol", [
    ("Pb", 661.66, 0.1101, 0.01), ("Pb", 1332.5, 0.0562, 0.015), ("Pb", 1000.0, 0.0710, 0.01),
    ("Al", 661.66, 0.0747, 0.01), ("Al", 1250.0, 0.0550, 0.015), ("H", 1000.0, 0.1263, 0.01),
])
def test_total_matches_nist(xs, sym, E, ref, tol):
    assert xs.total(sym, E)[0] == pytest.approx(ref, rel=tol)


def test_pair_production_is_smooth_near_threshold(xs_fisx):
    xs = xs_fisx
    """fisx returns garbage pair values between 1022 and ~1250 keV; the wrapper must fix that."""
    E = np.array([1000., 1022., 1050., 1100., 1173.228, 1250., 1300., 1332.492, 1400.])
    for sym in ("Ni", "Pb", "Bi", "Dy"):
        c = xs.components(sym, E)
        assert np.all(np.diff(c["pair"]) >= -1e-12)          # monotonic rising
        assert c["pair"][2] < 1e-4 and c["pair"][4] < 5e-4    # tiny just above threshold
        tot = c["total"]
        assert np.all(np.diff(tot) < 0)                      # total keeps falling
        # relative step between neighbours is smooth (no spike)
        assert np.max(np.abs(np.diff(np.log(tot)))) < 0.12


def test_atomic_weights():
    assert atomic_weight("Dy") == pytest.approx(162.5) and atomic_weight("O") == pytest.approx(15.999)


def test_csv_override(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("element,energy_keV,mu_rho_cm2_g\nPb,100,5.0\nPb,1000,0.05\n")
    xs = CrossSections(p)
    assert xs.total("Pb", 316.2278)[0] == pytest.approx(np.sqrt(5.0 * 0.05), rel=1e-3)   # log-log midpoint
    assert xs.total("Ni", 661.66)[0] > 0                                                  # falls back to built-in


def test_table_agrees_with_direct_fisx(xs, xs_fisx):
    """Interpolated table == direct calculation away from absorption edges (<0.1 %)."""
    rng = np.random.default_rng(0)
    worst = 0.0
    for sym in ("H", "O", "Al", "Ni", "Dy", "Bi", "Pb", "U"):
        E = np.exp(rng.uniform(np.log(25.0), np.log(3000.0), 400))
        a, b = xs.total(sym, E), xs_fisx.total(sym, E)
        rel = np.abs(a / b - 1)
        # discard points within 0.6 % of an absorption edge (jump inside one grid cell)
        jumps = np.flatnonzero(np.abs(np.diff(np.log(xs_fisx.total(sym, np.geomspace(10, 6000, 4000))))) > 0.05)
        edges = np.geomspace(10, 6000, 4000)[jumps]
        far = np.all(np.abs(E[:, None] / edges[None, :] - 1) > 0.006, axis=1) if edges.size else np.ones_like(E, bool)
        worst = max(worst, rel[far].max())
    assert worst < 1e-3


def test_table_range_error(xs):
    with pytest.raises(ValueError):
        xs.total("Pb", 5.0)
    with pytest.raises(KeyError):
        xs.total("Xx", 100.0)
