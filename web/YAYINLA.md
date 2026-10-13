# Web sürümünü Cloudflare'de yayınlama

Bu site **tamamen statik**tir: sunucuda hiçbir şey çalışmaz. Python (numpy/scipy) Pyodide ile ziyaretçinin
tarayıcısında çalışır, dosyalar bilgisayardan dışarı çıkmaz. Bu yüzden Cloudflare Pages yeterlidir
(ücretsiz plan dahil), Worker/veritabanı gerekmez.

## Hangi zip?

| Dosya | Boyut | Not |
|---|---|---|
| **`gama-zirhlama-web.zip`** (önerilen) | ≈1.7 MB | Pyodide'ı resmî jsDelivr CDN'inden (`cdn.jsdelivr.net/pyodide/v0.27.7/`) çeker; ziyaretçinin internet erişimi gerekir. |
| `gama-zirhlama-web-tam.zip` (isteğe bağlı) | ≈41 MB | Pyodide dosyaları içinde; hiçbir dış siteye bağımlı değil. Depoda tutulmaz; aşağıdaki "yeniden üretme" ile oluşturulur. |

İkisi de aynı arayüzdür; site kendi `pyodide/` klasörünü bulursa onu, bulamazsa CDN'i kullanır.
CDN'e erişilemezse sayfa "Hesaplama motoru yüklenemedi" uyarısı gösterir; o durumda tam sürümü kullanın.

## Adımlar (Cloudflare Pages – Direct Upload)

1. https://dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** → **Upload assets**
   (menü adları zamanla değişebilir: "Direct Upload" / "Upload your static files" aranır).
2. Proje adı yazın (örn. `gama-zirhlama`) → **Create project**.
3. Zip dosyasını sürükleyip bırakın (zip'in **kökünde** `index.html` olmalı; bu zipler öyledir) → **Deploy site**.
4. Birkaç saniye sonra `https://gama-zirhlama.pages.dev` adresinde yayında olur.
5. Kendi alan adınız için: proje → **Custom domains** → **Set up a custom domain** → örn. `zirhlama.siteadiniz.com`
   (alan adınız Cloudflare DNS'teyse kayıt otomatik eklenir).
   Ana sitenizin içinde `siteadiniz.com/zirhlama` gibi bir yol istiyorsanız en kolayı alt alan adı kullanıp ana
   siteden bağlantı vermektir (iframe ile gömmek de çalışır).

Güncelleme: aynı projede **Create deployment** ile yeni zip yükleyin.

## Notlar

* **Gizlilik:** Spektrum dosyaları sunucuya gönderilmez; analiz tarayıcıda yapılır. Sayfa `noindex` işaretlidir
  (arama motorlarında görünmez); herkese açık olsun istiyorsanız `index.html` içindeki `<meta name="robots">`
  satırını silip yeniden zipleyin. Yalnızca sizin kullanmanızı istiyorsanız Cloudflare Access ile e-posta
  doğrulaması ekleyebilirsiniz (Zero Trust → Access → Applications).
* **İlk açılış** birkaç saniye–yarım dakika sürer (≈40 MB kütüphane indirilir); sonra tarayıcı önbelleğinden gelir.
  Hesaplama süresi: 4 spektrum ≈ 30 sn, tek numune + I₀ ≈ 20 sn.
* **Tarayıcı:** güncel Chrome, Edge, Firefox veya Safari (WebAssembly + Web Worker gerekir).
* Numune bilgileri (kalınlık, yoğunluk, bileşim) tarayıcıda hatırlanır; "Ayarları dışa aktar" ile JSON olarak
  saklayıp başka bilgisayarda içe aktarabilirsiniz.

## Yerelde deneme / yeniden üretme

```bash
python tools/build_web.py                       # dist/site + dist/gama-zirhlama-web.zip (CDN'li küçük sürüm)
python tools/vendor_pyodide.py <pyodide-0.27.7 klasörü>   # dist/site_full + gama-zirhlama-web-tam.zip
python -m http.server -d dist/site_full 8000     # http://localhost:8000
python tests/e2e_web.py <pyodide klasörü> [chromium]      # tarayıcıda uçtan uca test (playwright)
```
Pyodide dağıtımı: https://github.com/pyodide/pyodide/releases/tag/0.27.7 (`pyodide-0.27.7.tar.bz2`).
Yalnızca `file://` ile açılan sayfa çalışmaz (Web Worker için bir HTTP sunucusu gerekir).
