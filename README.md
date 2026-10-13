# Gama zırhlama otomasyonu (.Spc → LAC ve tüm zırhlama parametreleri, hata paylarıyla)

ORTEC/MAESTRO **`.Spc`** spektrum dosyalarından (DSPEC-50, 4096 kanal) başlayarak

| Büyüklük | Hata payı |
|---|---|
| Net pik alanı / sayım hızı (her çizgi) | Poisson istatistiği + uyum kalitesi + **model (fon/pencere) belirsizliği** |
| **LAC μ** (cm⁻¹), T = I/I₀, RPE (%) | I₀, I, model, **kalınlık** |
| **MAC μ/ρ** (cm²/g) | + **yoğunluk** (tekrar ölçümlerinin standart hatası) |
| **HVL, TVL, MFP** (cm) | μ'den yayılım |
| **Zeff, Neff, Nₑ, σₐ, σₑ** | MAC'tan yayılım |
| Kuramsal (EPDL97) MAC, LAC, HVL, Zeff, Neff ve **deney–kuram sapması (%)** | — |
| Referans malzemeler (Pb, sıradan beton) için kuramsal HVL | — |
| Veriden **çıkarsanan kalınlık** (geometri/numune konumu kontrolü) | I₀, I, model |

hesaplar ve `output/` klasörüne **Excel, CSV, grafik ve Türkçe rapor** yazar.
Kapsam dışı (bilinçli): EBF/EABF (buildup) ve hızlı nötron ΣR.

## Hızlı başlangıç

```bash
pip install -r requirements.txt           # Python 3.10+ (fisx gerekmez; tesir kesiti tablosu pakette)
python -m gamma_shielding config/config.yaml      # veya Windows'ta calistir.bat'a çift tıklayın
```

1. `.Spc` dosyalarını `data/raw/` içine koyun (numunesiz ölçüm dahil).
2. `config/config.yaml` içinde:
   * `bos_olcum: dosya:` → numunesiz (I₀) spektrum dosya adı,
   * her numune için `kalinlik_mm:` (mikrometre okumaları, ör. `[2.01, 2.00, 2.02]`),
   * gerekirse `yogunluk_g_cm3`, `bilesim_agirlik` (ağırlık kesirleri).
3. Çalıştırın. Çıktılar:
   * `output/sonuclar.xlsx` – Özet, Parametreler, Pikler, Göreli zayıflama, Teorik, Referans malzeme, Numune bilgisi, Kalibrasyon, **Belirsizlik bütçesi**, Uyarılar, Yöntem
   * `output/csv/*.csv`, `output/rapor.md`, `output/grafikler/*.png`

**Eksik girdi olursa araç hata vermez; hesaplayabildiğini hesaplar ve ne eksik olduğunu `Uyarılar`'da söyler:**

| Girdi | Yoksa neyi hesaplayamaz |
|---|---|
| numunesiz (I₀) spektrum | LAC, MAC, HVL, TVL, MFP, RPE, Zeff, Neff (yalnızca pikler + göreli zayıflama) |
| `kalinlik_mm` | LAC, MAC, HVL, TVL, MFP, Zeff, Neff (T ve RPE yine hesaplanır) |
| `yogunluk_g_cm3` | MAC, Zeff, Neff, kuramsal LAC |
| `bilesim_agirlik` | Zeff, Neff, tüm kuramsal değerler |

## Web sürümü (tarayıcıda, sunucusuz)

Aynı kod **Pyodide** ile tarayıcıda çalışır: `.Spc` dosyalarını sürükleyin, kalınlık/yoğunluk/bileşimi formdan girin,
sonuçları (tablo, grafik, Excel, zip) indirin. Cloudflare Pages'e zip olarak yüklenir.

```bash
python tools/build_web.py                  # dist/gama-zirhlama-web.zip  (1.7 MB, Pyodide CDN'den)
python tools/vendor_pyodide.py <pyodide>   # dist/gama-zirhlama-web-tam.zip (41 MB, isteğe bağlı: dış bağımlılık yok)
```
Yayınlama adımları: [`web/YAYINLA.md`](web/YAYINLA.md). Tarayıcı sonuçları yerel Python ile
karşılaştırılarak doğrulanmıştır (net alan farkı < 2×10⁻⁴; `tests/e2e_web.py`).
Bileşim kutusu elementleri (`Ni 0.75; Al 0.15`) ya da bileşikleri (`Dy2O3 5; SiO2 60`) ağırlık veya mol olarak kabul eder.

## Yöntem (özet)

* **Kalibrasyon** her spektrum için ayrı ve otomatik: Ba-133/Cs-137/Co-60 tepeleri başlıktaki yaklaşık kalibrasyonla bulunur, 2. derece polinom uydurulur (başlıktaki kalibrasyon bu cihazda %3 kadar kaymış olabilir). Elle: `kalibrasyon: katsayilar: [c0, c1, c2]`.
* **Pik analizi:** ayrışmayan çoklu çizgiler tek grup olarak (Ba-133 356+384 keV, 276+303 keV, 79.6+81 keV), Gauss + polinom fon + Compton kenarı/basamak, **Poisson olabilirlik** (sapma) minimizasyonu. Belirsizlik Fisher bilgi matrisinden; uyum kötüyse √(χ²/ndf) (Birge) ile büyütülür.
* **Model belirsizliği:** fon derecesi, pencere genişliği ve yapısal alternatifler (basamak, σ bağlama, Compton kenarı) *aynı biçimde hem I₀'a hem numuneye* uygulanır; **ln(I₀/I)'nın varyantlar arası standart sapması** hata bütçesine eklenir (ortak sistematikler oranda kendiliğinden sönümlenir).
* **Sayım hızı** = net alan / canlı süre. Bozunma düzeltmesi isteğe bağlıdır (`bozunma_duzeltmesi`).
* Formüller ve belirsizlik yayılımı: `output/rapor.md` §8 ve `gamma_shielding/physics.py` başı.
* Kuramsal tesir kesitleri **EPDL97** (pakete gömülü tablo; `tools/make_xs_table.py` + `fisx` ile üretildi, doğrudan hesaba göre <%0.1) – XCOM ile 0.05–2 MeV'de tipik olarak %1–2 fark. **XCOM ile birebir** istiyorsanız elementel XCOM değerlerini `element,energy_keV,mu_rho_cm2_g` CSV'si olarak verip `xcom_csv:` ile bağlayın. (`fisx`'in çift oluşum sütunu 1022–1250 keV arasında hatalıdır; `xsec.py` bunu düzeltir – 1173 keV için önemli.)
* Yeni kaynak/çizgi: `gamma_shielding/lines.py` veya yapılandırmada `bolgeler:` ile (bkz. `config.py`).

## Doğrulama

`python -m pytest tests -m "not slow"` (41 test) ve `-m slow`:

* sentetik spektrumlarda (bilinen μ) 14 tekrar × 6 çizgi: **pull ortalaması +0.01, std 0.89** → yanlılık yok, hata payları doğru/hafif muhafazakâr;
* belirsizlik yayılımı Monte Carlo ile, Zeff (saf element → Z), kuramsal MAC (NIST: Pb, Al, H, su), çift oluşum düzeltmesi, `.Spc` okuyucu (gerçek dosyalar), yapılandırma hataları.

`examples/sentetik_ornek/` **gerçek veri değildir**; nihai çıktının biçimini göstermek için sentetik spektrumlardan üretilmiştir (`python examples/make_synthetic_example.py`).

## Bu veri seti için notlar

* Dedektör **NaI(Tl) benzeri** (662 keV'de FWHM ≈ %7). Tespit edilen çizgiler: Ba-133 81 / 303 / 356, Cs-137 662, Co-60 1173 / 1332 keV. **Am-241 (59.5) ve Co-57 (122) spektrumlarda görünmüyor** (net alan sıfırla uyumlu) → analiz dışı kalır.
* **Kurşun kolimatör:** ≈47 keV (Pb-210) ve ≈92 keV omuz (Pb K X-ışını bölgesi) yardımcı bileşen olarak modellenir; 81 keV çizgisinin sonuçları bu yüzden daha yüksek model belirsizliği taşır ve kolimatör floresansı numuneden geçen ışınla aynı şekilde zayıflamaz.
* **303 keV** çizgisi (276+303 keV) Compton zemini üzerinde zayıf; belirsizliği büyüktür.
* `.Spc` başlığındaki tarih/saat *kaydetme* zamanı olabilir (dosyalar arası 16 dk fark var); bozunma düzeltmesi için ölçüm başlangıçlarını `baslangic:` ile elle verin.
