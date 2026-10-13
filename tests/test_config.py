from pathlib import Path

import pytest

from gamma_shielding.config import ConfigError, load_config

ROOT = Path(__file__).resolve().parents[1]


def test_shipped_config_loads():
    cfg = load_config(ROOT / "config" / "config.yaml")
    assert [s.name for s in cfg.samples] == ["Dy-0", "Dy-5", "Dy-10", "Dy-20"]
    assert cfg.samples[1].density == [6.3123, 6.3090, 6.3181]
    assert cfg.samples[0].thickness_mm is None
    assert cfg.spectra_dir == ROOT / "data" / "raw"
    for s in cfg.samples:
        assert abs(sum(s.composition.values()) - 1.0) < 2e-4
        assert (cfg.spectra_dir / s.file).exists()


def test_bad_configs(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("numuneler: []\n")
    with pytest.raises(ConfigError):
        load_config(p)
    p.write_text("numuneler:\n  - ad: A\n    dosya: a.Spc\n  - ad: A\n    dosya: b.Spc\n")
    with pytest.raises(ConfigError):
        load_config(p)
    p.write_text("numuneler:\n  - ad: A\n")
    with pytest.raises(ConfigError):
        load_config(p)
    p.write_text("numuneler: [\n")
    with pytest.raises(ConfigError):
        load_config(p)


def test_thickness_list_and_scalar(tmp_path):
    p = tmp_path / "c.yaml"
    p.write_text("numuneler:\n  - ad: A\n    dosya: a.Spc\n    kalinlik_mm: 2.5\n"
                 "  - ad: B\n    dosya: b.Spc\n    kalinlik_mm: [2.0, 2.1, null]\n")
    cfg = load_config(p)
    assert cfg.samples[0].thickness_mm == [2.5] and cfg.samples[1].thickness_mm == [2.0, 2.1]
