"""Builds the static website (Cloudflare Pages / any static host) and the upload zip.

    python tools/build_web.py          ->  dist/site/   and   dist/gama-zirhlama-web.zip

The site runs the Python package in the browser with Pyodide; nothing is executed on the server.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"
PKG = ROOT / "gamma_shielding"
DIST = ROOT / "dist"
SITE = DIST / "site"
SKIP_PKG = {"cli.py", "__main__.py"}


def main():
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    for name in ("index.html", "style.css", "app.js", "worker.js", "_headers"):
        shutil.copy2(WEB / name, SITE / name)
    for sub in ("wheels", "demo"):
        shutil.copytree(WEB / sub, SITE / sub)

    files, h = [], hashlib.sha1()
    for f in sorted(PKG.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts or f.suffix == ".pyc" or f.name in SKIP_PKG:
            continue
        rel = f.relative_to(ROOT).as_posix()
        dst = SITE / "py" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
        h.update(rel.encode() + f.read_bytes())
        files.append({"path": rel, "size": f.stat().st_size})
    for name in ("app.js", "worker.js", "index.html", "style.css"):
        h.update((WEB / name).read_bytes())
    wheels = sorted(p.relative_to(WEB).as_posix() for p in (WEB / "wheels").glob("*.whl"))
    (SITE / "py" / "manifest.json").write_text(
        json.dumps({"build": h.hexdigest()[:10], "files": files, "wheels": wheels}, indent=1), encoding="utf-8")

    zpath = DIST / "gama-zirhlama-web.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(SITE.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(SITE).as_posix())
    total = sum(f.stat().st_size for f in SITE.rglob("*") if f.is_file())
    print(f"site: {SITE}  ({total / 1e6:.1f} MB, {sum(1 for _ in SITE.rglob('*') if _.is_file())} dosya)")
    print(f"zip : {zpath}  ({zpath.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
