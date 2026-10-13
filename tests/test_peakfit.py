import numpy as np
import pytest

from gamma_shielding.calibration import Calibration, find_anchors, fit_calibration
from gamma_shielding.peakfit import PeakSpec, RegionSpec, Resolution, fit_region, roi_sum_area

CAL = Calibration([0.0, 0.5, 1e-5], n_channels=4096)


def _gauss_spectrum(rng, area=20000.0, e0=661.66, bkg=700.0, slope=-0.1):
    ch = np.arange(4096.0)
    E = CAL.energy(ch)
    res = Resolution()
    sig_ch = res.sigma_keV(e0) / CAL.dE_dch(CAL.channel(e0))
    mu = float(CAL.channel(e0))
    from scipy.special import ndtr
    peak = area * (ndtr((ch + .5 - mu) / sig_ch) - ndtr((ch - .5 - mu) / sig_ch))
    y = bkg + slope * (ch - mu) + peak
    return rng.poisson(np.clip(y, 0, None)).astype(float)


def test_area_pulls_are_unit_normal():
    region = RegionSpec("Cs", 540, 800, (PeakSpec("Cs-137 662", (661.657,)),), bkg_order=1)
    pulls = []
    for seed in range(60):
        counts = _gauss_spectrum(np.random.default_rng(seed))
        f = fit_region(counts, CAL, region, Resolution())
        assert f.ok
        pk = f.peaks["Cs-137 662"]
        pulls.append((pk["area"] - 20000.0) / pk["u_area"])
    pulls = np.array(pulls)
    assert abs(pulls.mean()) < 0.35
    assert 0.75 < pulls.std(ddof=1) < 1.3


def test_doublet_group_shares_one_amplitude():
    grp = PeakSpec("Ba-133 356", (356.0129, 383.8485), (62.05, 8.94))
    assert grp.E_main == pytest.approx(356.0129)
    assert grp.E_eff == pytest.approx((356.0129 * 62.05 + 383.8485 * 8.94) / (62.05 + 8.94), rel=1e-6)
    assert sum(grp.weights) == pytest.approx(1.0)


def test_roi_sum_area_matches_truth_for_isolated_peak():
    counts = _gauss_spectrum(np.random.default_rng(3), area=50000.0, slope=0.0)
    c0 = int(CAL.channel(661.66))
    net, u = roi_sum_area(counts, c0 - 110, c0 + 110, n_bkg=10)
    assert abs(net - 50000.0 * 0.99) < 4 * u


def test_calibration_roundtrip_and_anchor_search():
    cal = Calibration([-1.0, 0.5, 1.3e-5], n_channels=4096)
    ch = np.arange(4096.0)
    rng = np.random.default_rng(0)
    y = 300.0 + np.zeros(4096)
    for e, a in ((81, 3000), (356, 6000), (661.66, 5000), (1173.2, 9000), (1332.5, 9000)):
        mu = float(cal.channel(e))
        s = Resolution().sigma_keV(e) / float(cal.dE_dch(mu))
        y += a / (s * np.sqrt(2 * np.pi)) * np.exp(-0.5 * ((ch - mu) / s) ** 2)
    counts = rng.poisson(y)
    anchors = [("a", 81.0), ("b", 356.0), ("c", 661.66), ("d", 1173.2), ("e", 1332.5)]
    found = find_anchors(counts, anchors, lambda c: 0.52 * np.asarray(c, float))     # 4 % wrong rough calibration
    assert len(found) == 5
    fit = fit_calibration(found, order=2)
    assert fit.rms_residual_keV < 2.0
    assert fit.energy(2000) == pytest.approx(cal.energy(2000), abs=3.0)
    assert fit.channel(fit.energy(1234.0)) == pytest.approx(1234.0, abs=1e-3)


def test_non_monotonic_calibration_rejected():
    with pytest.raises(ValueError):
        Calibration([0.0, 0.5, -1e-3], n_channels=4096)
