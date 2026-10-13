"""Builds the self-contained site (no CDN needed) by copying the required part of a Pyodide
distribution into dist/site_full/pyodide/ and zipping it.

    python tools/build_web.py
    python tools/vendor_pyodide.py <dir of the extracted pyodide-0.27.7.tar.bz2>

Needs the full Pyodide release (https://github.com/pyodide/pyodide/releases/tag/0.27.7).
"""

from __future__ import annotations

import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
NEEDED = ["numpy", "scipy", "pandas", "matplotlib", "pyyaml", "micropip"]
CORE = ["pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip"]


def closure(pk, names):
    seen, stack = set(), [n.lower().replace("_", "-") for n in names]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        if n not in pk:
            raise SystemExit(f"paket kilit dosyasinda yok: {n}")
        seen.add(n)
        stack += [d.lower().replace("_", "-") for d in pk[n]["depends"]]
    return seen


def main():
    src = Path(sys.argv[1])
    site = DIST / "site"
    full = DIST / "site_full"
    if not site.exists():
        raise SystemExit("once: python tools/build_web.py")
    if full.exists():
        shutil.rmtree(full)
    shutil.copytree(site, full)
    out = full / "pyodide"
    out.mkdir()
    lock = json.loads((src / "pyodide-lock.json").read_text())
    pk = lock["packages"]
    keep = closure(pk, NEEDED)
    lock["packages"] = {k: v for k, v in pk.items() if k in keep}
    (out / "pyodide-lock.json").write_text(json.dumps(lock))
    for f in CORE + [pk[k]["file_name"] for k in sorted(keep)]:
        shutil.copy2(src / f, out / f)
    zpath = DIST / "gama-zirhlama-web-tam.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(full.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(full).as_posix())
    total = sum(f.stat().st_size for f in full.rglob("*") if f.is_file())
    big = max((f.stat().st_size for f in full.rglob("*") if f.is_file()), default=0)
    print(f"site_full: {full} ({total / 1e6:.1f} MB, {len(keep)} paket, en buyuk dosya {big / 2**20:.1f} MiB)")
    print(f"zip: {zpath} ({zpath.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
