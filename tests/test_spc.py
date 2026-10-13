from pathlib import Path

import numpy as np
import pytest

from gamma_shielding.spc import SpcFormatError, read_spc

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
FILES = sorted(RAW.glob("*.Spc"))


@pytest.mark.skipif(not FILES, reason="ornek .Spc dosyalari yok")
def test_read_real_spc_header_and_counts():
    s = read_spc(RAW / "Dy2O3_00_5kaynak_2saat.Spc")
    assert s.n_channels == 4096
    assert s.live_time == pytest.approx(7200.0)
    assert s.real_time == pytest.approx(7383.74, abs=0.01)
    assert s.total_counts == 1900871
    assert s.name == "Dy2O3_00_5kaynak_2saat"
    assert s.start.year == 2026 and s.start.month == 10 and s.start.day == 13
    assert s.header_calibration[1] == pytest.approx(0.52077, abs=1e-4)
    assert 0.02 < s.dead_time_fraction < 0.03
    assert s.header_rois[0] == (135, 190)


def test_rejects_non_spc(tmp_path):
    p = tmp_path / "x.Spc"
    p.write_bytes(b"\x00" * 4096)
    with pytest.raises(SpcFormatError):
        read_spc(p)
    q = tmp_path / "tiny.Spc"
    q.write_bytes(b"abc")
    with pytest.raises(SpcFormatError):
        read_spc(q)
