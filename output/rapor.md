# Dy2O3 katkili Ni-Al-Bi numuneleri - gama zirhlama parametreleri

## 1. Durum

- Spektrum sayısı: 4 (numune: 4, numunesiz/I0: **YOK**)
- Kalınlık girilmiş mi: **hayır**; yoğunluk: evet; bileşim: evet
- **LAC, MAC, HVL, TVL, MFP, RPE, Zeff ve Neff henüz hesaplanamadı** (eksik girdi için bkz. Uyarılar).

## 2. Veri kontrolü ve kalibrasyon

| Spektrum | Toplam_sayim | Canli_sure_s | Gercek_sure_s | Olu_zaman_yuzde | Sayim_hizi_cps | RMS_artik_keV | Cozunurluk_FWHM_662_yuzde |
|---|---|---|---|---|---|---|---|
| Dy-0 | 1900871 | 7200 | 7384 | 2.488 | 264 | 3.532 | 7.057 |
| Dy-5 | 1908388 | 7200 | 7381 | 2.446 | 265.1 | 3.38 | 7.086 |
| Dy-10 | 1911828 | 7200 | 7382 | 2.463 | 265.5 | 3.491 | 7.204 |
| Dy-20 | 1901341 | 7200 | 7384 | 2.494 | 264.1 | 3.397 | 7.098 |

- Dy-0: `E[keV] = -0.0264256 + 0.501645*ch^1 + 1.34568e-05*ch^2`
- Dy-5: `E[keV] = 0.156686 + 0.499451*ch^1 + 1.43633e-05*ch^2`
- Dy-10: `E[keV] = -0.14625 + 0.501215*ch^1 + 1.3672e-05*ch^2`
- Dy-20: `E[keV] = -0.108171 + 0.50215*ch^1 + 1.33684e-05*ch^2`

## 3. Tespit edilen çizgiler (net alan, istatistik belirsizlik)

| Spektrum | Cizgi | E_nominal_keV | Alan ± u | Anlamlilik_sigma | FWHM_yuzde | chi2_ndf | Kabul_varyant |
|---|---|---|---|---|---|---|---|
| Dy-0 | Ba-133 81 | 80.9 | 31043 ± 577 | 53.76 | 13.97 | 1.093 | 6 |
| Dy-0 | Ba-133 303 | 295.4 | 18791 ± 1044 | 18 | 9.284 | 1.12 | 7 |
| Dy-0 | Ba-133 356 | 359.5 | 49965 ± 1208 | 41.37 | 8.586 | 1.12 | 7 |
| Dy-0 | Cs-137 662 | 661.7 | 41694 ± 798 | 52.27 | 7.162 | 1.014 | 7 |
| Dy-0 | Co-60 1173 | 1173 | 145652 ± 1099 | 132.5 | 5.795 | 1.002 | 7 |
| Dy-0 | Co-60 1332 | 1332 | 146837 ± 740 | 198.5 | 5.495 | 1.002 | 7 |
| Dy-5 | Ba-133 81 | 80.9 | 30652 ± 599 | 51.2 | 13.93 | 1.119 | 6 |
| Dy-5 | Ba-133 303 | 295.4 | 19687 ± 1010 | 19.5 | 9.498 | 1.04 | 7 |
| Dy-5 | Ba-133 356 | 359.5 | 52344 ± 1117 | 46.84 | 8.42 | 1.04 | 7 |
| Dy-5 | Cs-137 662 | 661.7 | 44466 ± 897 | 49.57 | 7.373 | 1.163 | 7 |
| Dy-5 | Co-60 1173 | 1173 | 146597 ± 1111 | 131.9 | 5.772 | 1.068 | 7 |
| Dy-5 | Co-60 1332 | 1332 | 147107 ± 750 | 196.1 | 5.476 | 1.068 | 7 |
| Dy-10 | Ba-133 81 | 80.9 | 30415 ± 635 | 47.88 | 13.85 | 1.364 | 6 |
| Dy-10 | Ba-133 303 | 295.4 | 21282 ± 1219 | 17.46 | 11.23 | 0.9795 | 7 |
| Dy-10 | Ba-133 356 | 359.5 | 51848 ± 1108 | 46.81 | 8.425 | 0.9795 | 7 |
| Dy-10 | Cs-137 662 | 661.7 | 43164 ± 825 | 52.32 | 7.232 | 1.03 | 7 |
| Dy-10 | Co-60 1173 | 1173 | 146235 ± 1108 | 131.9 | 5.727 | 1.083 | 7 |
| Dy-10 | Co-60 1332 | 1332 | 146781 ± 748 | 196.4 | 5.43 | 1.083 | 7 |
| Dy-20 | Ba-133 81 | 80.9 | 31511 ± 639 | 49.35 | 14.14 | 1.086 | 6 |
| Dy-20 | Ba-133 303 | 295.4 | 20864 ± 1191 | 17.52 | 10.12 | 1.248 | 7 |
| Dy-20 | Ba-133 356 | 359.5 | 51599 ± 1260 | 40.96 | 8.578 | 1.248 | 7 |
| Dy-20 | Cs-137 662 | 661.7 | 41126 ± 818 | 50.25 | 7.031 | 1.113 | 7 |
| Dy-20 | Co-60 1173 | 1173 | 147697 ± 1066 | 138.6 | 5.752 | 1.002 | 8 |
| Dy-20 | Co-60 1332 | 1332 | 148019 ± 720 | 205.6 | 5.455 | 1.002 | 8 |


## 4. Göreli zayıflama (bilgi amaçlı)

Referans: **Dy-0**. T = I/I_ref; ±: istatistik ⊕ model. (Bu tablo LAC değildir; numunesiz ölçüm yokken spektrumların tutarlılığını gösterir.)

| Numune | Cizgi | E_keV | T=I/Iref | u_T | Anlamlilik_sigma |
|---|---|---|---|---|---|
| Dy-5 | Ba-133 81 | 80.9 | 0.9874 | 0.02876 | 0.4344 |
| Dy-5 | Ba-133 303 | 295.4 | 1.048 | 0.08694 | 0.5613 |
| Dy-5 | Ba-133 356 | 359.5 | 1.048 | 0.03497 | 1.394 |
| Dy-5 | Cs-137 662 | 661.7 | 1.066 | 0.03813 | 1.8 |
| Dy-5 | Co-60 1173 | 1173 | 1.006 | 0.01309 | 0.4977 |
| Dy-5 | Co-60 1332 | 1332 | 1.002 | 0.007506 | 0.2458 |
| Dy-10 | Ba-133 81 | 80.9 | 0.9798 | 0.03019 | 0.6633 |
| Dy-10 | Ba-133 303 | 295.4 | 1.133 | 0.1008 | 1.399 |
| Dy-10 | Ba-133 356 | 359.5 | 1.038 | 0.03486 | 1.101 |
| Dy-10 | Cs-137 662 | 661.7 | 1.035 | 0.03035 | 1.183 |
| Dy-10 | Co-60 1173 | 1173 | 1.004 | 0.01122 | 0.3573 |
| Dy-10 | Co-60 1332 | 1332 | 0.9996 | 0.007175 | 0.05275 |
| Dy-20 | Ba-133 81 | 80.9 | 1.015 | 0.0312 | 0.4869 |
| Dy-20 | Ba-133 303 | 295.4 | 1.11 | 0.1169 | 0.9944 |
| Dy-20 | Ba-133 356 | 359.5 | 1.033 | 0.03657 | 0.9088 |
| Dy-20 | Cs-137 662 | 661.7 | 0.9864 | 0.03507 | 0.3858 |
| Dy-20 | Co-60 1173 | 1173 | 1.014 | 0.01201 | 1.178 |
| Dy-20 | Co-60 1332 | 1332 | 1.008 | 0.007862 | 1.028 |


## 6. Kuramsal değerler (karışım kuralı, EPDL97)

| Numune | Cizgi | E_keV | MAC_kuram_cm2_g | LAC_kuram_cm-1 | HVL_kuram_cm | Zeff_kuram | Neff_kuram_e_g |
|---|---|---|---|---|---|---|---|
| Dy-0 | Ba-133 81 | 80.9 | 0.8091 | 5.151 | 0.1346 | 33.28 | 3.771e+23 |
| Dy-0 | Ba-133 303 | 295.4 | 0.1462 | 0.9307 | 0.7447 | 30.14 | 3.416e+23 |
| Dy-0 | Ba-133 356 | 359.5 | 0.1213 | 0.7723 | 0.8976 | 28.6 | 3.241e+23 |
| Dy-0 | Cs-137 662 | 661.7 | 0.07923 | 0.5044 | 1.374 | 26.2 | 2.968e+23 |
| Dy-0 | Co-60 1173 | 1173 | 0.05729 | 0.3648 | 1.9 | 25.48 | 2.887e+23 |
| Dy-0 | Co-60 1332 | 1332 | 0.05355 | 0.3409 | 2.033 | 25.42 | 2.88e+23 |
| Dy-5 | Ba-133 81 | 80.9 | 1.03 | 6.501 | 0.1066 | 38.08 | 4.272e+23 |
| Dy-5 | Ba-133 303 | 295.4 | 0.1525 | 0.963 | 0.7198 | 31.12 | 3.492e+23 |
| Dy-5 | Ba-133 356 | 359.5 | 0.1249 | 0.7887 | 0.8788 | 29.33 | 3.291e+23 |
| Dy-5 | Cs-137 662 | 661.7 | 0.07976 | 0.5035 | 1.377 | 26.51 | 2.974e+23 |
| Dy-5 | Co-60 1173 | 1173 | 0.05725 | 0.3614 | 1.918 | 25.66 | 2.879e+23 |
| Dy-5 | Co-60 1332 | 1332 | 0.05347 | 0.3376 | 2.053 | 25.59 | 2.871e+23 |
| Dy-10 | Ba-133 81 | 80.9 | 1.25 | 7.843 | 0.08838 | 41.99 | 4.666e+23 |
| Dy-10 | Ba-133 303 | 295.4 | 0.1589 | 0.997 | 0.6952 | 32.07 | 3.564e+23 |
| Dy-10 | Ba-133 356 | 359.5 | 0.1286 | 0.8068 | 0.8592 | 30.04 | 3.338e+23 |
| Dy-10 | Cs-137 662 | 661.7 | 0.08029 | 0.5038 | 1.376 | 26.82 | 2.98e+23 |
| Dy-10 | Co-60 1173 | 1173 | 0.0572 | 0.3589 | 1.931 | 25.84 | 2.871e+23 |
| Dy-10 | Co-60 1332 | 1332 | 0.0534 | 0.3351 | 2.069 | 25.76 | 2.862e+23 |
| Dy-20 | Ba-133 81 | 80.9 | 1.688 | 10.61 | 0.06536 | 47.99 | 5.227e+23 |
| Dy-20 | Ba-133 303 | 295.4 | 0.1715 | 1.077 | 0.6434 | 33.91 | 3.694e+23 |
| Dy-20 | Ba-133 356 | 359.5 | 0.1358 | 0.8529 | 0.8127 | 31.46 | 3.427e+23 |
| Dy-20 | Cs-137 662 | 661.7 | 0.08134 | 0.5109 | 1.357 | 27.45 | 2.99e+23 |
| Dy-20 | Co-60 1173 | 1173 | 0.05711 | 0.3587 | 1.932 | 26.21 | 2.855e+23 |
| Dy-20 | Co-60 1332 | 1332 | 0.05324 | 0.3344 | 2.073 | 26.11 | 2.844e+23 |


## 7. Uyarılar

- 'Dy-0' referansina gore hicbir numunede hicbir cizgide 3 sigma'yi asan fark yok: spektrumlar istatistiksel olarak ayirt edilemiyor. Numunenin isin yolunda oldugundan ve kalinligin yeterli oldugundan emin olun (numunesiz olcumle karsilastirinca netlesir).
- Spektrumlarda tespit edilemeyen cizgiler (analiz disi birakildi): Am-241 59.5 (en yuksek 2.2 sigma); Co-57 122 (en yuksek 2.1 sigma)
- Numunesiz (I0) spektrum tanimli degil: LAC/MAC/HVL/TVL/MFP/RPE/Zeff/Neff hesaplanmadi.

## 8. Yöntem

- **Net alan:** Her çizgi grubu (ör. Ba-133 356+384 keV) Gauss + polinom fon (+ Compton kenarı / basamak) modeliyle Poisson olabilirlik (sapma) minimizasyonu ile uydurulur. Alan belirsizliği Fisher bilgi matrisinden hesaplanır; uyum chi2/ndf>1 ise sqrt(chi2/ndf) (Birge) ile büyütülür.
- **Model belirsizliği:** Fon derecesi, uydurma penceresi ve yapısal alternatiflerle (basamak, sigma bağı, Compton kenarı) aynı analiz tüm spektrumlara uygulanır. u_model = ln(I0/I) değerlerinin varyantlar arasındaki standart sapması (ortak sistematik etkiler oranda otomatik sönümlenir).
- **Sayım hızı:** I = net alan / canlı süre (DSPEC ölü zamanı canlı süre ile düzeltilir).
- **L:** L = ln(I0/I);  u_L² = (u_I0/I0)² + (u_I/I)² + u_model²
- **LAC:** μ = L/x;  u_μ² = (u_L/x)² + (μ u_x/x)²
- **MAC:** μ/ρ = μ/ρ;  u² = (u_μ/ρ)² + (μ u_ρ/ρ²)²  (ρ: deneysel yoğunluk ortalaması ± standart hata)
- **HVL, TVL, MFP:** ln2/μ, ln10/μ, 1/μ;  göreli belirsizlik = u_μ/μ  (yalnızca μ ≥ 3 u_μ ise güvenilir)
- **RPE:** RPE = (1 − I/I0)×100;  u = 100·(I/I0)·u_L
- **Zeff, Neff:** Doğrudan yöntem: σ_a = (μ/ρ)/(N_A Σ w_i/A_i);  σ_e = (1/N_A) Σ f_i (A_i/Z_i)(μ/ρ)_i;  Zeff = σ_a/σ_e;  Neff = (μ/ρ)/σ_e;  Ne = Neff·ρ. Elementel (μ/ρ)_i değerleri EPDL97 (XCOM ailesi).
- **Kuramsal:** Karışım kuralı: μ/ρ = Σ w_i (μ/ρ)_i; kuramsal LAC = (μ/ρ)·ρ_deneysel.
- **Kapsam:** Tablolar 1σ standart belirsizlik taşır; 'Özet' sayfası yapılandırmadaki kapsam katsayısı k ile verilir.
