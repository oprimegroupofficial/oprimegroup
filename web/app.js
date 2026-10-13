/* Gama Zırhlama Analizi – arayüz.  Hesaplama worker.js içindeki Pyodide motorunda yapılır. */
"use strict";

const $ = (s, r = document) => r.querySelector(s);
const h = (tag, attrs = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k === "html") e.innerHTML = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v !== false && v != null) e.setAttribute(k, v === true ? "" : v);
  }
  for (const c of kids.flat()) if (c != null) e.append(c.nodeType ? c : document.createTextNode(c));
  return e;
};
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const BASE_DEFAULT = "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/";   // 'pyodide' sorgu parametresiyle değiştirilebilir
const params = new URLSearchParams(location.search);
const norm = (u) => u.replace(/\/?$/, "/");
/* Pyodide konumu: ?pyodide=… > sitenin kendi pyodide/ klasörü (tam paket) > jsDelivr CDN */
async function pickBase() {
  if (params.get("pyodide")) return norm(params.get("pyodide"));
  try {
    const r = await fetch("pyodide/pyodide-lock.json", { cache: "no-cache" });
    if (r.ok) { const j = await r.json(); if (j && j.packages) return new URL("pyodide/", location.href).href; }
  } catch (e) { /* yerel kopya yok */ }
  return BASE_DEFAULT;
}

const DEMO = [   // gönderilen Dy2O3 serisi (kalınlık bilinmediği için boş)
  { file: "Dy2O3_00_5kaynak_2saat.Spc", label: "Dy-0", density: "6.3748 6.3794 6.3459", theo: "6.66", comp: "Ni 0.7497; Al 0.1501; Bi 0.1002" },
  { file: "Dy2O3_05_5kaynak_2saat.Spc", label: "Dy-5", density: "6.3123 6.3090 6.3181", theo: "6.63", comp: "Ni 0.6999; Al 0.1498; Bi 0.1002; Dy 0.0437; O 0.0065" },
  { file: "Dy2O3_10_5kaynak_2saat.Spc", label: "Dy-10", density: "6.2684 6.2597 6.2975", theo: "6.59", comp: "Ni 0.6495; Al 0.1501; Bi 0.1002; Dy 0.0873; O 0.0129" },
  { file: "Dy2O3_20_5kaynak_2saat.Spc", label: "Dy-20", density: "6.2435 6.2984 6.3006", theo: "6.53", comp: "Ni 0.5498; Al 0.1501; Bi 0.1002; Dy 0.1742; O 0.0257" },
];

const state = {
  files: [], meta: {}, nextId: 1, ready: false, running: false, result: null,
  allLines: [], excluded: new Set(), xcomPath: null, blobs: {},
};

/* ------------------------------------------------------------------ motor (worker) */
class Engine {
  constructor() { this.pending = new Map(); this.seq = 0; this.onStatus = () => {}; this.onProgress = () => {}; this.start(); }
  start() {
    this.worker = new Worker("worker.js");
    this.worker.onmessage = (e) => this.onMsg(e.data);
    this.worker.onerror = (e) => this.fail(new Error(e.message || "worker hatası"));
  }
  call(type, payload = {}, transfer = []) {
    return new Promise((resolve, reject) => {
      const id = ++this.seq;
      this.pending.set(id, { resolve, reject });
      this.worker.postMessage({ type, id, ...payload }, transfer);
    });
  }
  onMsg(m) {
    if (m.type === "status") this.onStatus(m);
    else if (m.type === "progress") this.onProgress(m);
    else if (m.type === "result") {
      const p = this.pending.get(m.id);
      if (!p) return;
      this.pending.delete(m.id);
      m.ok ? p.resolve(m.value) : p.reject(Object.assign(new Error(m.error), { stack: m.stack }));
    }
  }
  fail(err) { for (const p of this.pending.values()) p.reject(err); this.pending.clear(); }
  terminate() { this.worker.terminate(); this.fail(new Error("iptal edildi")); }
}

let engine = null, engineReady = null;

function bootEngine() {
  engine = new Engine();
  setChip("loading", "Hesaplama motoru yükleniyor…", 0.02);
  engine.onStatus = (m) => setChip(m.frac >= 1 ? "ready" : "loading", m.frac >= 1 ? "Hesaplama motoru hazır" : m.text, m.frac);
  engineReady = pickBase().then((base) => engine.call("init", {
    base, siteBase: new URL("./", location.href).href,
  })).then(async (v) => {
    state.ready = true;
    state.allLines = await engine.call("lines");
    renderLineList();
    refreshRunState();
    return v;
  }).catch((e) => {
    setChip("fail", "Motor yüklenemedi: " + e.message, 0);
    console.error(e);
    $("#fileMsgs").append(h("div", { class: "banner err" },
      "Hesaplama motoru yüklenemedi. İnternet bağlantınızı kontrol edip sayfayı yenileyin. (", e.message, ")"));
    throw e;
  });
  return engineReady;
}

function setChip(kind, text, frac) {
  const chip = $("#engineChip");
  chip.className = "chip " + (kind === "ready" ? "ready" : kind === "fail" ? "fail" : "");
  $("#engineText").textContent = text;
  $("#engineBar").style.width = Math.round((frac || 0) * 100) + "%";
}

/* ------------------------------------------------------------------ yardımcılar */
function parseNums(text) {
  const t = String(text || "").replace(/(?<=\d),(?=\d)/g, ".");
  const toks = t.split(/[;\s,]+/).filter(Boolean);
  const out = toks.map(Number);
  return { vals: out, bad: toks.filter((_, i) => Number.isNaN(out[i])) };
}
function stats(v) {
  const n = v.length, m = v.reduce((a, b) => a + b, 0) / n;
  const sd = n > 1 ? Math.sqrt(v.reduce((a, b) => a + (b - m) ** 2, 0) / (n - 1)) : 0;
  return { n, m, sem: n > 1 ? sd / Math.sqrt(n) : 0 };
}
function fmtPM(v, u) {
  if (!Number.isFinite(v)) return "–";
  if (!(u > 0)) return fmtNum(v);
  const dec = Math.min(10, Math.max(0, 1 - Math.floor(Math.log10(u))));
  return `${v.toFixed(dec)} ± ${u.toFixed(dec)}`;
}
const LABELS = {
  Spektrum: "Spektrum", Cizgi: "Çizgi", Kaynak: "Kaynak", Numune: "Numune", E_keV: "E (keV)", E_nominal_keV: "E (keV)", E_uydurma_keV: "E uydurma (keV)",
  FWHM_keV: "FWHM (keV)", FWHM_yuzde: "FWHM (%)", Net_alan: "Net alan", u_alan_ist: "u(alan), istatistik", Anlamlilik_sigma: "Anlamlılık (σ)",
  Hiz_cps: "Hız (cps)", u_hiz_ist_cps: "u(hız) (cps)", chi2_ndf: "χ²/ndf", ndf: "ndf", Kabul_varyant: "Kabul edilen varyant", Red_varyant: "Reddedilen varyant",
  Alan_model_dagilimi_yuzde: "Alan model dağılımı (%)", Canli_sure_s: "Canlı süre (s)", Gercek_sure_s: "Gerçek süre (s)", Tespit: "Tespit", Uydurma_notu: "Uydurma notu",
  Referans: "Referans", "T=I/Iref": "T = I/I_ref", u_T: "u(T)", "ln(Iref/I)": "ln(I_ref/I)", u_ist: "u istatistik", u_model: "u model", u_toplam: "u toplam", Model_varyant_sayisi: "Model varyant sayısı",
  I0_cps: "I₀ (cps)", u_I0_cps: "u(I₀)", I_cps: "I (cps)", u_I_cps: "u(I)", T_I_I0: "T = I/I₀", L_ln_I0_I: "L = ln(I₀/I)", u_L_ist: "u(L) istatistik", u_L_model: "u(L) model", u_L: "u(L)",
  Bozunma_duzeltme_carpani: "Bozunma düzeltme çarpanı", RPE_yuzde: "RPE (%)", u_RPE_yuzde: "u(RPE) (%)", L_anlamlilik_sigma: "L anlamlılık (σ)",
  x_cm: "x (cm)", u_x_cm: "u(x) (cm)", "LAC_cm-1": "LAC μ (cm⁻¹)", "u_LAC_cm-1": "u(LAC)", LAC_anlamlilik_sigma: "LAC anlamlılık (σ)",
  HVL_cm: "HVL (cm)", u_HVL_cm: "u(HVL)", TVL_cm: "TVL (cm)", u_TVL_cm: "u(TVL)", MFP_cm: "MFP (cm)", u_MFP_cm: "u(MFP)",
  rho_g_cm3: "ρ (g/cm³)", u_rho_g_cm3: "u(ρ)", MAC_cm2_g: "MAC μ/ρ (cm²/g)", u_MAC_cm2_g: "u(MAC)", Zeff: "Zeff", u_Zeff: "u(Zeff)",
  Neff_e_g: "Neff (e/g)", u_Neff_e_g: "u(Neff)", Ne_e_cm3: "Nₑ (e/cm³)", u_Ne_e_cm3: "u(Nₑ)", sigma_a_barn: "σₐ (barn)", u_sigma_a_barn: "u(σₐ)", sigma_e_barn: "σₑ (barn)",
  "LAC_kuram_cm-1": "LAC kuramsal (cm⁻¹)", MAC_kuram_cm2_g: "MAC kuramsal (cm²/g)", HVL_kuram_cm: "HVL kuramsal (cm)", TVL_kuram_cm: "TVL kuramsal (cm)", MFP_kuram_cm: "MFP kuramsal (cm)",
  Zeff_kuram: "Zeff kuramsal", Neff_kuram_e_g: "Neff kuramsal (e/g)", Ne_kuram_e_cm3: "Nₑ kuramsal (e/cm³)", Sapma_MAC_yuzde: "Sapma MAC (%)", u_Sapma_MAC_yuzde: "u(sapma) (%)",
  Kalinlik_cikarsanan_mm: "Çıkarsanan kalınlık (mm)", u_Kalinlik_cikarsanan_mm: "u(çıkarsanan kalınlık)", Not: "Not",
  Katki_ist_I0: "katkı: ist. I₀", Katki_ist_I: "katkı: ist. I", Katki_model: "katkı: model", Katki_kalinlik: "katkı: kalınlık",
  Kalibrasyon: "Kalibrasyon", RMS_artik_keV: "RMS artık (keV)", Cozunurluk_FWHM_662_yuzde: "FWHM 662 keV (%)", Toplam_sayim: "Toplam sayım", Olu_zaman_yuzde: "Ölü zaman (%)", Sayim_hizi_cps: "Sayım hızı (cps)",
  MAC_cm2_g_: "", Malzeme: "Malzeme",
};
const label = (k) => LABELS[k] || k.replaceAll("_", " ");
function fmtNum(v) {
  if (v === null || v === undefined || v === "") return "–";
  if (typeof v !== "number") return String(v);
  if (!Number.isFinite(v)) return "–";
  const a = Math.abs(v);
  if (a !== 0 && (a >= 1e5 || a < 1e-3)) return v.toExponential(3);
  return String(Number(v.toPrecision(5)));
}
function saveMeta() {
  try {
    const store = JSON.parse(localStorage.getItem("gz_meta_v1") || "{}");
    for (const f of state.files) if (f.role === "sample") store[f.label] = state.meta[f.id];
    localStorage.setItem("gz_meta_v1", JSON.stringify(store));
  } catch (e) { /* özel pencere vb. */ }
}
function loadMetaFor(label) {
  try { return JSON.parse(localStorage.getItem("gz_meta_v1") || "{}")[label]; } catch (e) { return null; }
}
const emptyMeta = () => ({ thickness: "", thickness_u_mm: 0.01, density: "", theo_density: "", composition: "", composition_mode: "wt" });

/* ------------------------------------------------------------------ dosyalar */
async function writeFile(id, blob) {
  await engineReady;
  const path = `/data/f${id}.Spc`;
  const buf = await blob.arrayBuffer();
  await engine.call("write", { path, buffer: buf }, [buf]);
  return path;
}

async function addBlobs(items) {   // items: [{blob, file, label?, meta?}]
  await engineReady;
  const added = [];
  for (const it of items) {
    const id = state.nextId++;
    const path = await writeFile(id, it.blob);
    state.blobs[id] = it.blob;
    added.push({ id, path, file: it.file, label: it.label, meta: it.meta });
  }
  const info = await engine.call("inspect", { items: added.map((a) => ({ path: a.path, name: a.file })) });
  added.forEach((a, i) => {
    const r = info[i];
    const f = { id: a.id, path: a.path, file: a.file, info: r, role: r.ok ? r.role : "ignore", label: a.label || (r.ok ? r.label : a.file) };
    state.meta[a.id] = Object.assign(emptyMeta(), loadMetaFor(f.label) || {}, a.meta || {});
    state.files.push(f);
    if (!r.ok) $("#fileMsgs").append(h("div", { class: "banner err" }, `${a.file}: ${r.error}`));
  });
  uniqueLabels();
  renderFiles();
}
function uniqueLabels() {
  const seen = {};
  for (const f of state.files) {
    if (f.role === "ignore") continue;
    const base = f.label;
    seen[base] = (seen[base] || 0) + 1;
    if (seen[base] > 1) f.label = `${base} (${seen[base]})`;
  }
}

function renderFiles() {
  const rows = $("#fileRows");
  rows.replaceChildren();
  $("#fileTableWrap").hidden = state.files.length === 0;
  $("#clearBtn").hidden = state.files.length === 0;
  for (const f of state.files) {
    const r = f.info;
    const sel = h("select", { "aria-label": "Rol", onchange: (e) => { f.role = e.target.value; if (f.role === "blank") { for (const o of state.files) if (o !== f && o.role === "blank") o.role = "sample"; } renderFiles(); } },
      h("option", { value: "sample", selected: f.role === "sample" }, "Numune"),
      h("option", { value: "blank", selected: f.role === "blank" }, "Numunesiz (I₀)"),
      h("option", { value: "ignore", selected: f.role === "ignore" }, "Yoksay"));
    const name = h("input", { value: f.label, "aria-label": "Ad", oninput: (e) => { f.label = e.target.value; const t = $(`#sc${f.id} .ttl`); if (t) t.textContent = f.label; } , onchange: () => { saveMeta(); } });
    rows.append(h("tr", {},
      h("td", { title: f.file }, f.file),
      h("td", { class: "num" }, r.ok ? r.counts.toLocaleString("tr-TR") : "–"),
      h("td", { class: "num" }, r.ok ? fmtNum(r.live_time) : "–"),
      h("td", { class: "num" }, r.ok ? r.dead_pct.toFixed(1) + " %" : "–"),
      h("td", {}, r.ok ? sel : "geçersiz"),
      h("td", { style: "min-width:150px" }, f.role === "blank" ? h("span", { class: "pill" }, "I₀") : r.ok ? name : ""),
      h("td", {}, h("button", { class: "link danger", type: "button", onclick: () => removeFile(f.id) }, "Kaldır"))));
  }
  renderSamples();
  refreshRunState();
}
async function removeFile(id) {
  const i = state.files.findIndex((f) => f.id === id);
  if (i < 0) return;
  const [f] = state.files.splice(i, 1);
  delete state.blobs[id];
  await engine.call("remove", { path: f.path });
  renderFiles();
}

/* ------------------------------------------------------------------ numune kartları */
function renderSamples() {
  const box = $("#samples");
  const samples = state.files.filter((f) => f.role === "sample" && f.info.ok);
  $("#s2").hidden = samples.length === 0;
  box.replaceChildren();
  for (const f of samples) {
    const m = state.meta[f.id];
    const hint = (cls = "") => h("div", { class: "hint " + cls });
    const hT = hint(), hD = hint(), hC = hint();
    const upd = () => { updNum(hT, m.thickness, "mm"); updNum(hD, m.density, "g/cm³"); saveMeta(); };
    const upComp = debounce(async () => {
      if (!String(m.composition).trim()) { hC.textContent = "Boş: Zeff/Neff ve kuramsal değerler hesaplanmaz."; hC.className = "hint"; return; }
      if (!state.ready) { hC.textContent = "Motor yükleniyor…"; return; }
      const r = await engine.call("parse_comp", { text: m.composition, mode: m.composition_mode });
      if (r.ok) {
        const parts = Object.entries(r.fractions).sort((a, b) => b[1] - a[1]).map(([k, v]) => `${k} ${(100 * v).toFixed(2)} %`);
        hC.textContent = "Ağırlıkça: " + parts.join(", "); hC.className = "hint ok";
      } else { hC.textContent = r.error; hC.className = "hint bad"; }
      saveMeta();
    }, 350);
    const inp = (label, key, attrs = {}, hintEl) => h("div", {}, h("label", { for: `${key}${f.id}` }, label),
      h("input", Object.assign({ id: `${key}${f.id}`, value: m[key], oninput: (e) => { m[key] = e.target.value; upd(); } }, attrs)), hintEl);
    const comp = h("textarea", { id: `comp${f.id}`, rows: 2, spellcheck: false, placeholder: "Ni 0.7497; Al 0.1501; Bi 0.1002   veya   Dy2O3 5; SiO2 60; B2O3 35",
      oninput: (e) => { m.composition = e.target.value; upComp(); } }, m.composition);
    const modeSel = h("select", { id: `mode${f.id}`, onchange: (e) => { m.composition_mode = e.target.value; upComp(); } },
      h("option", { value: "wt", selected: m.composition_mode === "wt" }, "Ağırlık (kesir veya %)"),
      h("option", { value: "mol", selected: m.composition_mode === "mol" }, "Mol (mol %)"));
    const card = h("div", { class: "scard", id: `sc${f.id}` },
      h("h3", {}, h("span", { class: "ttl" }, f.label), h("span", { class: "small" }, f.file)),
      h("div", { class: "grid" },
        inp("Kalınlık (mm) – okumalar", "thickness", { placeholder: "örn. 2.01 2.00 2.02", inputmode: "decimal" }, hT),
        inp("Kalınlık ölçer belirsizliği (mm)", "thickness_u_mm", { type: "number", step: "0.001", min: "0" }),
        inp("Yoğunluk (g/cm³) – okumalar", "density", { placeholder: "örn. 6.3748 6.3794 6.3459", inputmode: "decimal" }, hD),
        inp("Kuramsal yoğunluk (isteğe bağlı)", "theo_density", { placeholder: "6.66", inputmode: "decimal" }),
        h("div", { class: "wide" }, h("label", { for: `comp${f.id}` }, "Bileşim"), comp, hC),
        h("div", {}, h("label", { for: `mode${f.id}` }, "Bileşim birimi"), modeSel)));
    box.append(card);
    updNum(hT, m.thickness, "mm", true); updNum(hD, m.density, "g/cm³", true); upComp();
  }
}
function updNum(el, text, unit, quiet) {
  const t = String(text || "").trim();
  if (!t) { el.className = "hint"; el.textContent = unit === "mm" ? "Boş: LAC, MAC, HVL, TVL, MFP, Zeff hesaplanmaz." : "Boş: MAC, Zeff, Neff ve kuramsal LAC hesaplanmaz."; return; }
  const { vals, bad } = parseNums(t);
  if (bad.length) { el.className = "hint bad"; el.textContent = `'${bad[0]}' sayı değil – okumaları boşluk veya ';' ile ayırın.`; return; }
  const s = stats(vals);
  el.className = "hint ok";
  el.textContent = `${s.n} okuma: ortalama ${s.n > 1 ? fmtPM(s.m, s.sem) : fmtNum(s.m)} ${unit}` + (s.n > 1 ? " (± standart hata)" : "");
}
function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

/* ------------------------------------------------------------------ ayarlar */
function renderLineList() {
  const box = $("#lineList");
  box.replaceChildren();
  for (const l of state.allLines) {
    box.append(h("label", {}, h("input", { type: "checkbox", checked: state.excluded.has(l), onchange: (e) => { e.target.checked ? state.excluded.add(l) : state.excluded.delete(l); } }), l));
  }
}
$("#xcomFile").addEventListener("change", async (e) => {
  const f = e.target.files[0];
  if (!f) { state.xcomPath = null; return; }
  await engineReady;
  const buf = await f.arrayBuffer();
  await engine.call("write", { path: "/data/xcom.csv", buffer: buf }, [buf]);
  state.xcomPath = "/data/xcom.csv";
  $("#xcomHint").textContent = `${f.name} yüklendi; belirtilen element/enerji aralıkları için XCOM değerleri kullanılacak.`;
});
$("#exportBtn").addEventListener("click", () => {
  const data = { version: 1, settings: { k: $("#optK").value, sig: $("#optSig").value, xs: $("#optXs").value, variants: $("#optVar").checked },
    samples: Object.fromEntries(state.files.filter((f) => f.role === "sample").map((f) => [f.label, state.meta[f.id]])) };
  saveBlob(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }), "gama_ayarlar.json");
});
$("#importBtn").addEventListener("click", () => $("#importFile").click());
$("#importFile").addEventListener("change", async (e) => {
  const f = e.target.files[0]; if (!f) return;
  try {
    const d = JSON.parse(await f.text());
    if (d.settings) { $("#optK").value = d.settings.k ?? 1; $("#optSig").value = d.settings.sig ?? 5; $("#optXs").value = d.settings.xs ?? 0; $("#optVar").checked = d.settings.variants !== false; }
    const store = JSON.parse(localStorage.getItem("gz_meta_v1") || "{}");
    Object.assign(store, d.samples || {}); localStorage.setItem("gz_meta_v1", JSON.stringify(store));
    for (const fl of state.files) if (fl.role === "sample" && d.samples?.[fl.label]) state.meta[fl.id] = Object.assign(emptyMeta(), d.samples[fl.label]);
    renderSamples();
  } catch (err) { $("#fileMsgs").append(h("div", { class: "banner err" }, "Ayar dosyası okunamadı: " + err.message)); }
});

/* ------------------------------------------------------------------ çalıştırma */
function refreshRunState() {
  const nS = state.files.filter((f) => f.role === "sample" && f.info.ok).length;
  const nB = state.files.filter((f) => f.role === "blank").length;
  const btn = $("#runBtn");
  btn.disabled = !state.ready || state.running || nS === 0;
  $("#runHint").textContent = !state.ready ? "Hesaplama motoru yükleniyor…" : nS === 0 ? "Önce en az bir numune spektrumu yükleyin."
    : `${nS} numune${nB ? " + numunesiz (I₀)" : " (numunesiz ölçüm yok: yalnızca pik tablosu ve göreli zayıflama üretilir)"}`;
}
function buildPayload() {
  const files = state.files.filter((f) => f.info.ok).map((f) => ({ path: f.path, role: f.role, name: f.label }));
  const samples = {};
  for (const f of state.files) if (f.role === "sample") samples[f.path] = state.meta[f.id];
  return {
    project: "Gama zırhlama analizi", files, samples,
    settings: { k: +$("#optK").value, min_sig: +$("#optSig").value, variants: $("#optVar").checked,
      exclude_lines: [...state.excluded], xcom_csv: state.xcomPath, xs_rel_unc: (+$("#optXs").value || 0) / 100 },
  };
}
async function run() {
  state.running = true; refreshRunState();
  $("#runProg").hidden = false; $("#cancelBtn").hidden = false;
  setRun(0.01, "Başlıyor…");
  engine.onProgress = (m) => setRun(m.frac, m.text);
  const t0 = performance.now();
  try {
    const resp = await engine.call("analyze", { payload: buildPayload() });
    state.result = resp;
    setRun(1, `Tamamlandı (${((performance.now() - t0) / 1000).toFixed(0)} s)`);
    showResults(resp);
  } catch (e) {
    if (String(e.message).includes("iptal")) return;
    showResults({ ok: false, error: e.message, detail: e.stack });
  } finally {
    state.running = false; $("#cancelBtn").hidden = true; refreshRunState();
  }
}
function setRun(frac, text) { $("#runBar").style.width = Math.round(frac * 100) + "%"; $("#runText").textContent = text; }
$("#runBtn").addEventListener("click", run);
$("#cancelBtn").addEventListener("click", async () => {
  engine.terminate(); state.ready = false; state.running = false;
  $("#runProg").hidden = true; $("#cancelBtn").hidden = true;
  await bootEngine();                                   // dosyalar yeniden yazılır
  for (const f of state.files) await writeFile(f.id, state.blobs[f.id]);
  refreshRunState();
});

/* ------------------------------------------------------------------ sonuçlar */
const TABS = [];
function showResults(r) {
  const box = $("#results");
  box.hidden = false;
  const banners = $("#banners");
  banners.replaceChildren();
  $("#tabs").replaceChildren(); $("#tabBody").replaceChildren();
  if (!r.ok) {
    banners.append(h("div", { class: "banner err" }, h("strong", {}, "Analiz yapılamadı: "), r.error,
      r.detail ? h("details", {}, h("summary", {}, "Ayrıntı"), h("div", { class: "err-detail" }, r.detail)) : null));
    box.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  const st = r.status;
  const chips = [["Numunesiz (I₀)", st.blank], ["Kalınlık", st.thickness_all], ["Yoğunluk", st.density_all], ["Bileşim", st.composition_all]];
  banners.append(h("div", { class: "row small" }, chips.map(([n, ok]) => h("span", { class: "pill", style: `background:var(--${ok ? "ok" : "warn"}-soft);color:var(--${ok ? "ok" : "warn"})` }, (ok ? "✓ " : "✗ ") + n))));
  if (r.warnings.length) banners.append(h("div", { class: "banner warn" }, h("strong", {}, "Uyarılar"), h("ul", {}, r.warnings.map((w) => h("li", {}, w)))));
  else banners.append(h("div", { class: "banner ok" }, "Uyarı yok."));
  if (r.has_blank && r.attenuation.length && r.attenuation.some((a) => a["LAC_cm-1"] != null)) {
    banners.append(h("div", { class: "banner ok" }, `Tablolardaki ± değerleri k = ${r.coverage_k} kapsam katsayısıyla verilmiştir (istatistik + model + kalınlık/yoğunluk).`));
  }
  const tabs = [
    ["ozet", "Özet", () => summaryTab(r)],
    ["sayi", "Sayısal sonuçlar", () => tableTab(r.attenuation, null, "Numunesiz (I₀) ölçüm ve kalınlık girildiğinde dolar.")],
    ["pik", "Pikler", () => tableTab(r.peaks, ["Spektrum", "Cizgi", "E_nominal_keV", "Net_alan", "u_alan_ist", "Anlamlilik_sigma", "FWHM_yuzde", "chi2_ndf", "Kabul_varyant", "Alan_model_dagilimi_yuzde", "Tespit"])],
    ["goreli", "Göreli zayıflama", () => tableTab(r.relative, null, "", "Referansa göre T = I/I_ref. Numunesiz ölçüm yoksa ilk numune referans alınır; bu LAC değildir.")],
    ["kuram", "Kuramsal", () => tableTab(r.theory, null, "Bileşim girildiğinde dolar.")],
    ["butce", "Belirsizlik bütçesi", () => tableTab(r.budget, null, "LAC hesaplandığında dolar.")],
    ["kal", "Kalibrasyon", () => tableTab(r.calibration, ["Spektrum", "Kalibrasyon", "RMS_artik_keV", "Cozunurluk_FWHM_662_yuzde", "Toplam_sayim", "Olu_zaman_yuzde", "Sayim_hizi_cps"])],
    ["graf", "Grafikler", () => galleryTab(r)],
    ["indir", "İndir", () => downloadTab(r)],
  ];
  const tb = $("#tabs");
  tabs.forEach(([id, label, fn], i) => {
    const b = h("button", { role: "tab", "aria-selected": i === 0 ? "true" : "false", onclick: () => select(id) }, label);
    b.dataset.id = id; tb.append(b);
  });
  const select = async (id) => {
    for (const b of tb.children) b.setAttribute("aria-selected", b.dataset.id === id ? "true" : "false");
    const body = $("#tabBody"); body.replaceChildren(h("div", { class: "small" }, "Yükleniyor…"));
    body.replaceChildren(await tabs.find((t) => t[0] === id)[2]());
  };
  select("ozet");
  box.scrollIntoView({ behavior: "smooth", block: "start" });
}

function tableTab(rows, cols, emptyMsg = "", note = "") {
  const wrap = h("div");
  if (note) wrap.append(h("p", { class: "small" }, note));
  if (!rows || !rows.length) { wrap.append(h("p", { class: "small" }, emptyMsg || "Veri yok.")); return wrap; }
  const keys = cols || [...new Set(rows.flatMap((r) => Object.keys(r)))];
  const t = h("table", {},
    h("thead", {}, h("tr", {}, keys.map((k) => h("th", {}, label(k))))),
    h("tbody", {}, rows.map((r) => h("tr", {}, keys.map((k) => h("td", { class: typeof r[k] === "number" ? "num" : "" }, fmtNum(r[k])))))));
  wrap.append(h("div", { class: "tw", style: "max-height:70vh" }, t));
  return wrap;
}
function summaryTab(r) {
  if (!r.has_blank) {
    return h("div", {}, h("div", { class: "banner warn" }, "Numunesiz (I₀) ölçüm yüklenmediği için LAC, MAC, HVL, TVL, MFP, RPE, Zeff ve Neff henüz hesaplanamadı. I₀ spektrumunu ekleyip rolünü “Numunesiz (I₀)” yapın ve analizi yeniden çalıştırın."),
      h("h3", {}, "Tespit edilen çizgiler"), tableTab(r.peaks.filter((p) => p.Tespit === "evet"), ["Spektrum", "Cizgi", "E_nominal_keV", "Net_alan", "u_alan_ist", "Anlamlilik_sigma", "chi2_ndf"]),
      h("h3", {}, "Göreli zayıflama"), tableTab(r.relative, ["Numune", "Cizgi", "E_keV", "T=I/Iref", "u_T", "Anlamlilik_sigma"]));
  }
  const wrap = h("div");
  const ti = r.thickness_implied && Object.entries(r.thickness_implied);
  wrap.append(tableTab(r.summary, null, "Veri yok."));
  if (ti && ti.length) wrap.append(h("p", { class: "small" }, "Veriden çıkarsanan kalınlık (kuramsal μ ile): " + ti.map(([k, v]) => `${k}: ${fmtPM(v[0], v[1])} mm`).join("; ") + ". Ölçülen kalınlıkla uyumlu olmalıdır (geometri kontrolü)."));
  return wrap;
}
async function galleryTab(r) {
  const files = await engine.call("read", { paths: r.files.filter((f) => f.name.endsWith(".png")).map((f) => f.path) });
  const titles = { goreli_zayiflama: "Göreli zayıflama (ln I_ref/I)", lac_enerji: "LAC – enerji", mac_enerji: "MAC – enerji", hvl_enerji: "HVL – enerji", zeff_enerji: "Zeff – enerji", rpe_enerji: "RPE – enerji" };
  const g = h("div", { class: "gallery" });
  for (const f of r.files.filter((f) => f.name.endsWith(".png"))) {
    const base = f.name.split("/").pop().replace(".png", "");
    const url = URL.createObjectURL(new Blob([files[f.path]], { type: "image/png" }));
    const cap = titles[base] || (base.startsWith("spektrum_") ? "Spektrum ve pik uydurmaları: " + base.slice(9).replaceAll("_", " ") : base);
    g.append(h("figure", {}, h("img", { src: url, alt: cap, loading: "lazy", onclick: () => { $("#imgBig").src = url; $("#imgDlg").showModal(); } }), h("figcaption", {}, cap)));
  }
  return g.children.length ? g : h("p", { class: "small" }, "Grafik yok.");
}
function downloadTab(r) {
  const main = [["gama_zirhlama_sonuclar.zip", "Tümünü indir (.zip)"], ["sonuclar.xlsx", "Excel çalışma kitabı"], ["rapor.md", "Rapor (Markdown)"]];
  const dl = h("div", { class: "dl" });
  for (const [name, label] of main) {
    const f = r.files.find((x) => x.name === name); if (!f) continue;
    dl.append(h("div", {}, h("button", { class: name.endsWith(".zip") ? "primary" : "", type: "button", onclick: () => downloadPath(f.path, name) }, label), h("span", { class: "small" }, "  " + (f.size / 1024).toFixed(0) + " KB")));
  }
  dl.append(h("details", {}, h("summary", {}, "Tüm dosyalar"), h("div", { class: "dl", style: "margin-top:8px" }, r.files.filter((f) => !main.some((m) => m[0] === f.name)).map((f) =>
    h("div", {}, h("button", { class: "link", type: "button", onclick: () => downloadPath(f.path, f.name.split("/").pop()) }, f.name), h("span", { class: "small" }, " " + (f.size / 1024).toFixed(1) + " KB"))))));
  return dl;
}
async function downloadPath(path, name) {
  const out = await engine.call("read", { paths: [path] });
  saveBlob(new Blob([out[path]]), name);
}
function saveBlob(blob, name) {
  const a = h("a", { href: URL.createObjectURL(blob), download: name });
  document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 10000);
}

/* ------------------------------------------------------------------ olaylar */
const drop = $("#drop"), input = $("#fileInput");
drop.addEventListener("click", () => input.click());
drop.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); } });
["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => addBlobs([...e.dataTransfer.files].map((f) => ({ blob: f, file: f.name }))));
input.addEventListener("change", () => { addBlobs([...input.files].map((f) => ({ blob: f, file: f.name }))); input.value = ""; });
$("#clearBtn").addEventListener("click", async () => { for (const f of [...state.files]) await removeFile(f.id); $("#fileMsgs").replaceChildren(); });
$("#demoBtn").addEventListener("click", async () => {
  const btn = $("#demoBtn"); btn.disabled = true;
  try {
    const items = [];
    for (const d of DEMO) {
      const r = await fetch("demo/" + d.file); if (!r.ok) throw new Error(d.file + " indirilemedi");
      items.push({ blob: await r.blob(), file: d.file, label: d.label, meta: { density: d.density, theo_density: d.theo, composition: d.comp, composition_mode: "wt" } });
    }
    await addBlobs(items);
  } catch (e) { $("#fileMsgs").append(h("div", { class: "banner err" }, e.message)); }
  btn.disabled = false;
});
$("#imgDlg").addEventListener("click", () => $("#imgDlg").close());

if (!window.Worker || !window.WebAssembly) {
  $("#fileMsgs").append(h("div", { class: "banner err" }, "Bu tarayıcı WebAssembly/Web Worker desteklemiyor; güncel Chrome, Edge, Firefox veya Safari kullanın."));
} else {
  bootEngine().catch(() => {});
}
window.__gz = { state, get engine() { return engine; } };   // hata ayıklama / otomatik test için
