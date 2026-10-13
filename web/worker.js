/* Hesaplama motoru: Pyodide (tarayıcıda Python) + gamma_shielding paketi.  Ağır işler burada çalışır,
   böylece sayfa donmaz. */
"use strict";
let pyodide = null, api = null, base = null;

function status(text, frac) { postMessage({ type: "status", text, frac }); }

async function init(opts) {
  base = opts.base;                                   // Pyodide dağıtım adresi (sonu '/')
  importScripts(base + "pyodide.js");
  status("Python çalışma zamanı yükleniyor…", 0.05);
  pyodide = await loadPyodide({ indexURL: base });
  status("Bilimsel kütüphaneler yükleniyor (numpy, scipy, pandas, matplotlib)…", 0.15);
  await pyodide.loadPackage(["numpy", "scipy", "pandas", "matplotlib", "pyyaml", "micropip"]);
  status("Excel kütüphanesi yükleniyor…", 0.75);
  const manifest = await (await fetch(new URL("py/manifest.json", opts.siteBase), { cache: "no-cache" })).json();
  opts.version = manifest.build;
  const micropip = pyodide.pyimport("micropip");
  for (const w of manifest.wheels) await micropip.install(new URL(w, opts.siteBase).href, { deps: false });
  status("Analiz paketi hazırlanıyor…", 0.85);
  pyodide.FS.mkdirTree("/pkg");
  let n = 0;
  for (const f of manifest.files) {
    const dir = "/pkg/" + f.path.split("/").slice(0, -1).join("/");
    pyodide.FS.mkdirTree(dir);
    const buf = new Uint8Array(await (await fetch(new URL("py/" + f.path + "?v=" + opts.version, opts.siteBase))).arrayBuffer());
    pyodide.FS.writeFile("/pkg/" + f.path, buf);
    status("Analiz paketi hazırlanıyor… (" + (++n) + "/" + manifest.files.length + ")", 0.85);
  }
  pyodide.FS.mkdirTree("/data");
  status("Python kütüphaneleri başlatılıyor (ilk açılışta birkaç saniye sürebilir)…", 0.92);
  await pyodide.runPythonAsync(`
import os, sys
os.environ["MPLBACKEND"] = "Agg"
sys.path.insert(0, "/pkg")
import numpy, scipy.optimize, scipy.signal, scipy.ndimage, scipy.special, pandas
`);
  status("Grafik ve Excel modülleri başlatılıyor…", 0.96);
  await pyodide.runPythonAsync(`
import matplotlib, matplotlib.pyplot, openpyxl, yaml
from gamma_shielding import web_api
`);
  api = pyodide.pyimport("gamma_shielding.web_api");
  status("Hazır", 1);
}

const handlers = {
  async init(m) { await init(m); return { version: pyodide.version }; },
  async write(m) { pyodide.FS.writeFile(m.path, new Uint8Array(m.buffer)); return true; },
  async remove(m) { try { pyodide.FS.unlink(m.path); } catch (e) { /* yok say */ } return true; },
  async inspect(m) { return JSON.parse(api.inspect_files(JSON.stringify(m.items))); },
  async lines() { return JSON.parse(api.available_lines()); },
  async parse_comp(m) { return JSON.parse(api.parse_comp(m.text, m.mode)); },
  async analyze(m) {
    const progress = (msg, frac) => postMessage({ type: "progress", text: msg, frac });
    const out = api.analyze(JSON.stringify(m.payload), progress);
    return JSON.parse(out);
  },
  async read(m) {
    const out = {}, transfer = [];
    for (const p of m.paths) {
      const u8 = pyodide.FS.readFile(p);
      const copy = u8.slice().buffer;                 // kendi belleğimize kopya (transfer edilebilir)
      out[p] = copy; transfer.push(copy);
    }
    return { __transfer: transfer, value: out };
  },
};

onmessage = async (ev) => {
  const m = ev.data;
  try {
    const res = await handlers[m.type](m);
    if (res && res.__transfer) postMessage({ type: "result", id: m.id, ok: true, value: res.value }, res.__transfer);
    else postMessage({ type: "result", id: m.id, ok: true, value: res });
  } catch (err) {
    postMessage({ type: "result", id: m.id, ok: false, error: String(err && err.message || err), stack: String(err && err.stack || "") });
  }
};
