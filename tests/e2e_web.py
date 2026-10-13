"""Manual end-to-end test of the browser version in headless Chromium (not part of the pytest run).

    python tests/e2e_web.py <pyodide-0.27.7-dir> [chromium-executable]

Serves dist/site and a local copy of the Pyodide distribution (via ?pyodide=/pyodide/), loads the
demo spectra, runs the analysis in the browser, then repeats with a synthetic blank + thickness
and checks numbers against the native Python pipeline.
"""

from __future__ import annotations

import functools
import os
import http.server
import json
import math
import socketserver
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from playwright.sync_api import sync_playwright  # noqa: E402

import synthetic as sy  # noqa: E402
from gamma_shielding import physics as ph  # noqa: E402
from gamma_shielding.xsec import CrossSections  # noqa: E402
from spc_writer import spc_bytes  # noqa: E402


class Handler(http.server.SimpleHTTPRequestHandler):
    pyodide_dir = ""
    site_dir = os.environ.get("E2E_SITE") or str(ROOT / "dist" / "site")

    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/pyodide/") and not (Path(self.site_dir) / "pyodide").exists():
            return str(Path(self.pyodide_dir) / p[len("/pyodide/"):])
        return str(Path(self.site_dir) / p.lstrip("/"))

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *a):
        pass


def serve(pyodide_dir, port=8772):
    Handler.pyodide_dir = pyodide_dir
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", port), Handler)
    httpd.allow_reuse_address = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def main():
    pyodide_dir = sys.argv[1]
    exe = sys.argv[2] if len(sys.argv) > 2 else None
    httpd = serve(pyodide_dir)
    base = "http://127.0.0.1:8772/" + ("" if os.environ.get("E2E_NOPARAM") else "?pyodide=/pyodide/")
    tmp = Path(os.environ.get("E2E_OUT") or tempfile.mkdtemp())
    tmp.mkdir(parents=True, exist_ok=True)
    xs = CrossSections()
    from gamma_shielding.composition import parse_composition
    comp = parse_composition("Ni 0.7497; Al 0.1501; Bi 0.1002")
    LINES = {"Ba-133 81": 80.8991, "Ba-133 303": 295.4176, "Ba-133 356": 359.5183, "Cs-137 662": 661.657,
             "Co-60 1173": 1173.228, "Co-60 1332": 1332.492}
    rho, x_mm = 6.37, 2.0
    T = {k: math.exp(-ph.theory_point(xs, comp, E).mu_rho * rho * x_mm / 10) for k, E in LINES.items()}
    (tmp / "Bos_sentetik.Spc").write_bytes(spc_bytes(sy.make_spectrum("b", None, 11).counts, 7200, 7380, name="Bos", cal=sy.HEADER_CAL))
    (tmp / "Numune_sentetik.Spc").write_bytes(spc_bytes(sy.make_spectrum("s", T, 12).counts, 7200, 7380, name="Num", cal=sy.HEADER_CAL))

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe, args=["--no-sandbox"]) if exe else p.chromium.launch(args=["--no-sandbox"])
        ctx = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        logs = []
        page.on("console", lambda m: logs.append(f"[{m.type}] {m.text}"))
        page.on("pageerror", lambda e: logs.append(f"[pageerror] {e}"))
        t0 = time.time()
        page.goto(base)
        page.wait_for_function("document.querySelector('#engineText').textContent.includes('hazır')", timeout=600_000)
        print(f"motor hazir: {time.time() - t0:.0f} s")
        page.wait_for_function("window.__gz.state.allLines.length > 0", timeout=60_000)

        # ---- senaryo 1: demo veri, numunesiz ölçüm yok -------------------------------------------------
        page.click("#demoBtn")
        page.wait_for_function("window.__gz.state.files.length === 4", timeout=60_000)
        assert page.locator("#fileRows tr").count() == 4
        page.screenshot(path=str(tmp / "s1_files.png"), full_page=True)
        t1 = time.time()
        page.click("#runBtn")
        page.wait_for_function("!document.querySelector('#results').hidden", timeout=900_000)
        print(f"analiz 1 (4 spektrum): {time.time() - t1:.0f} s")
        res = page.evaluate("window.__gz.state.result")
        assert res["ok"], res
        assert not res["has_blank"]
        areas = {(r["Spektrum"], r["Cizgi"]): r["Net_alan"] for r in res["peaks"]}
        print("Dy-0 Cs-137 662 alan:", areas[("Dy-0", "Cs-137 662")])
        page.screenshot(path=str(tmp / "s1_results.png"), full_page=True)
        banners = page.inner_text("#banners")
        assert "Numunesiz" in banners
        # tabs
        for tab in ("Pikler", "Göreli zayıflama", "Kuramsal", "Grafikler", "İndir"):
            page.click(f"#tabs button:has-text('{tab}')")
            page.wait_for_timeout(500)
        page.click("#tabs button:has-text('Grafikler')")
        page.wait_for_function("document.querySelectorAll('.gallery img').length >= 5", timeout=60_000)
        page.screenshot(path=str(tmp / "s1_gallery.png"), full_page=True)
        n_img = page.locator(".gallery img").count()
        print("grafik sayisi:", n_img)

        # native karsilastirma
        from gamma_shielding.config import load_config
        from gamma_shielding.pipeline import run
        native = run(load_config(ROOT / "config" / "config.yaml"), xs)
        nat = {(r.Spektrum, r.Cizgi): r.Net_alan for r in native.peaks.itertuples()}
        worst = max(abs(areas[k] / nat[k] - 1) for k in nat if k in areas)
        print(f"tarayici vs yerel Python net alan farki (en kotu): {worst:.2e}")
        assert worst < 5e-3, worst

        # ---- senaryo 2: sentetik I0 + kalınlık -----------------------------------------------------------
        page.click("#clearBtn")
        page.wait_for_function("window.__gz.state.files.length === 0", timeout=30_000)
        page.set_input_files("#fileInput", [str(tmp / "Bos_sentetik.Spc"), str(tmp / "Numune_sentetik.Spc")])
        page.wait_for_function("window.__gz.state.files.length === 2", timeout=60_000)
        roles = page.evaluate("window.__gz.state.files.map(f => f.role)")
        assert sorted(roles) == ["blank", "sample"], roles
        page.fill("input[id^=thickness]", "2,00; 2.01 1.99")
        page.fill("input[id^=density]", "6,36; 6,37; 6,38")
        page.fill("textarea[id^=comp]", "Ni 0.7497; Al 0.1501; Bi 0.1002")
        page.wait_for_timeout(800)
        hint = page.inner_text(".scard")
        assert "Ağırlıkça" in hint and "Ni 74.97" in hint, hint
        page.click("summary:has-text('Gelişmiş ayarlar')")
        page.select_option("#optK", "2")
        t2 = time.time()
        page.click("#runBtn")
        page.wait_for_function("window.__gz.state.result && window.__gz.state.result.has_blank !== undefined && !window.__gz.state.running", timeout=900_000)
        print(f"analiz 2 (blank + numune): {time.time() - t2:.0f} s")
        res2 = page.evaluate("window.__gz.state.result")
        assert res2["ok"], res2
        att = {r["Cizgi"]: r for r in res2["attenuation"]}
        r = att["Cs-137 662"]
        mu_true = ph.theory_point(xs, comp, 661.657).mu_rho * rho
        print(f"Cs-137 662: LAC={r['LAC_cm-1']:.4f} ± {r['u_LAC_cm-1']:.4f} (gercek {mu_true:.4f}), HVL={r['HVL_cm']:.3f}")
        assert abs(r["LAC_cm-1"] - mu_true) < 4 * r["u_LAC_cm-1"]
        page.click("#tabs button:has-text('Özet')")
        page.wait_for_timeout(500)
        page.screenshot(path=str(tmp / "s2_results.png"), full_page=True)
        txt = page.inner_text("#tabBody")
        assert "±" in txt and "Cs-137 662" in txt
        # indirme
        page.click("#tabs button:has-text('İndir')")
        with page.expect_download(timeout=60_000) as dl:
            page.click("button:has-text('Tümünü indir')")
        zpath = tmp / "indirilen.zip"
        dl.value.save_as(str(zpath))
        import zipfile
        names = zipfile.ZipFile(zpath).namelist()
        print("zip icerigi:", names[:6], "...", len(names))
        assert "sonuclar.xlsx" in names
        import openpyxl
        z = zipfile.ZipFile(zpath); z.extract("sonuclar.xlsx", tmp)
        wb = openpyxl.load_workbook(tmp / "sonuclar.xlsx")
        print("excel sayfalari:", wb.sheetnames)
        errs = [l for l in logs if l.startswith("[pageerror]") or l.startswith("[error]")]
        print("konsol hatalari:", errs[:5])
        browser.close()
    print("EKRAN GORUNTULERI:", tmp)
    print("OK")


if __name__ == "__main__":
    main()
