"""Command line entry point:  python -m gamma_shielding config/config.yaml"""

from __future__ import annotations

import argparse
import sys

from .config import ConfigError, load_config


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gamma_shielding",
                                 description=".Spc spektrumlarindan LAC ve gama zirhlama parametreleri (hata paylariyla)")
    ap.add_argument("config", nargs="?", default="config/config.yaml", help="YAML yapilandirma dosyasi")
    args = ap.parse_args(argv)
    try:
        cfg = load_config(args.config)
        from .pipeline import run
        from .report import write_all
        from .xsec import CrossSections

        xs = CrossSections(cfg.xs_csv)
        res = run(cfg, xs)
        out = write_all(res, xs)
    except (ConfigError, FileNotFoundError, RuntimeError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2
    print(f"Tamamlandi. Ciktilar: {out}")
    print(f"  - {out / 'sonuclar.xlsx'}  (tum tablolar)")
    print(f"  - {out / 'rapor.md'}       (ozet rapor)")
    print(f"  - {out / 'grafikler'}      (grafikler)")
    for w in res.warnings:
        print("UYARI:", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
