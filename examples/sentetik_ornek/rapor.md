# SENTETIK ORNEK - GERCEK VERI DEGILDIR (yalnizca cikti bicimini gostermek icin)

## 1. Durum

- Spektrum sayısı: 3 (numune: 2, numunesiz/I0: var)
- Kalınlık girilmiş mi: evet; yoğunluk: evet; bileşim: evet

## 2. Veri kontrolü ve kalibrasyon

| Spektrum | Toplam_sayim | Canli_sure_s | Gercek_sure_s | Olu_zaman_yuzde | Sayim_hizi_cps | RMS_artik_keV | Cozunurluk_FWHM_662_yuzde |
|---|---|---|---|---|---|---|---|
| Bos (I0) | 2773269 | 7200 | 7380 | 2.439 | 385.2 | 0.2121 | 7.066 |
| ORNEK-A | 2719537 | 7200 | 7380 | 2.439 | 377.7 | 0.1602 | 7.027 |
| ORNEK-B | 2707852 | 7200 | 7380 | 2.439 | 376.1 | 0.04781 | 7.001 |

- Bos (I0): `E[keV] = -0.390149 + 0.501217*ch^1 + 1.31125e-05*ch^2`
- ORNEK-A: `E[keV] = -0.212649 + 0.50142*ch^1 + 1.30318e-05*ch^2`
- ORNEK-B: `E[keV] = -0.155598 + 0.501027*ch^1 + 1.3217e-05*ch^2`

## 3. Tespit edilen çizgiler (net alan, istatistik belirsizlik)

| Spektrum | Cizgi | E_nominal_keV | Alan ± u | Anlamlilik_sigma | FWHM_yuzde | chi2_ndf | Kabul_varyant |
|---|---|---|---|---|---|---|---|
| Bos (I0) | Ba-133 81 | 80.9 | 30423 ± 773 | 39.38 | 13.65 | 0.7342 | 6 |
| Bos (I0) | Ba-133 303 | 295.4 | 18994 ± 1060 | 17.93 | 9.295 | 0.9613 | 7 |
| Bos (I0) | Ba-133 356 | 359.5 | 48803 ± 1210 | 40.34 | 8.428 | 0.9613 | 7 |
| Bos (I0) | Cs-137 662 | 661.7 | 41935 ± 1000 | 41.91 | 7.156 | 1.137 | 7 |
| Bos (I0) | Co-60 1173 | 1173 | 147319 ± 1687 | 87.33 | 5.858 | 0.9965 | 8 |
| Bos (I0) | Co-60 1332 | 1332 | 147128 ± 1175 | 125.2 | 5.566 | 0.9965 | 8 |
| ORNEK-A | Ba-133 81 | 80.9 | 10760 ± 642 | 16.76 | 13.95 | 0.8726 | 6 |
| ORNEK-A | Ba-133 303 | 295.4 | 16525 ± 1061 | 15.57 | 9.094 | 1.039 | 7 |
| ORNEK-A | Ba-133 356 | 359.5 | 43171 ± 1266 | 34.09 | 8.609 | 1.039 | 7 |
| ORNEK-A | Cs-137 662 | 661.7 | 37721 ± 890 | 42.38 | 6.923 | 0.8758 | 7 |
| ORNEK-A | Co-60 1173 | 1173 | 137193 ± 1757 | 78.07 | 5.871 | 1.064 | 8 |
| ORNEK-A | Co-60 1332 | 1332 | 137401 ± 1223 | 112.4 | 5.58 | 1.064 | 8 |
| ORNEK-B | Ba-133 81 | 80.9 | 2735 ± 316 | 8.645 | 9.483 | 0.9769 | 6 |
| ORNEK-B | Ba-133 303 | 295.4 | 14123 ± 1006 | 14.03 | 8.828 | 0.9639 | 7 |
| ORNEK-B | Ba-133 356 | 359.5 | 40362 ± 1172 | 34.43 | 8.257 | 0.9639 | 7 |
| ORNEK-B | Cs-137 662 | 661.7 | 38223 ± 961 | 39.76 | 7.149 | 1.067 | 7 |
| ORNEK-B | Co-60 1173 | 1173 | 137199 ± 1683 | 81.52 | 5.912 | 0.965 | 8 |
| ORNEK-B | Co-60 1332 | 1332 | 137152 ± 1178 | 116.4 | 5.629 | 0.965 | 8 |


## 4. Göreli zayıflama (bilgi amaçlı)

Referans: **numunesiz ölçüm (I0)**. T = I/I0; ±: istatistik ⊕ model (kalınlık/yoğunluk belirsizliği hariç).

| Numune | Cizgi | E_keV | T=I/Iref | u_T | Anlamlilik_sigma |
|---|---|---|---|---|---|
| ORNEK-A | Ba-133 81 | 80.9 | 0.3537 | 0.02575 | 14.27 |
| ORNEK-A | Ba-133 303 | 295.4 | 0.87 | 0.09019 | 1.343 |
| ORNEK-A | Ba-133 356 | 359.5 | 0.8846 | 0.03658 | 2.966 |
| ORNEK-A | Cs-137 662 | 661.7 | 0.8995 | 0.03083 | 3.09 |
| ORNEK-A | Co-60 1173 | 1173 | 0.9313 | 0.02904 | 2.283 |
| ORNEK-A | Co-60 1332 | 1332 | 0.9339 | 0.01418 | 4.506 |
| ORNEK-B | Ba-133 81 | 80.9 | 0.08989 | 0.01166 | 18.57 |
| ORNEK-B | Ba-133 303 | 295.4 | 0.7436 | 0.08859 | 2.487 |
| ORNEK-B | Ba-133 356 | 359.5 | 0.8271 | 0.03323 | 4.726 |
| ORNEK-B | Cs-137 662 | 661.7 | 0.9115 | 0.03481 | 2.426 |
| ORNEK-B | Co-60 1173 | 1173 | 0.9313 | 0.01651 | 4.015 |
| ORNEK-B | Co-60 1332 | 1332 | 0.9322 | 0.01208 | 5.419 |


## 5. Sonuçlar

Tablo değerleri k = 2 kapsam katsayısıyla verilmiştir.

| Numune | Çizgi | E (keV) | T = I/I0 | RPE (%) | LAC μ (cm⁻¹) | MAC μ/ρ (cm²/g) | HVL (cm) | TVL (cm) | MFP (cm) | Zeff | Neff (e/g) | Çıkarsanan kalınlık (mm) | Not |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ORNEK-A | Ba-133 81 | 80.9 | 0.354 ± 0.052 | 64.6 ± 5.2 | 5.20 ± 0.73 | 0.82 ± 0.11 | 0.133 ± 0.019 | 0.443 ± 0.062 | 0.192 ± 0.027 | 33.6 ± 4.7 | (3.80 ± 0.53)e23 | 2.02 ± 0.28 |  |
| ORNEK-A | Ba-133 303 | 295.4 | 0.870 ± 0.180 | 13 ± 18 | 0.7 ± 1.0 | 0.11 ± 0.16 | 1.0 ± 1.5 | 3.3 ± 4.9 | 1.4 ± 2.1 | 23 ± 34 | (2.6 ± 3.8)e23 | 1.49 ± 2.23 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-A | Ba-133 356 | 359.5 | 0.885 ± 0.073 | 11.5 ± 7.3 | 0.61 ± 0.41 | 0.096 ± 0.065 | 1.13 ± 0.76 | 3.8 ± 2.5 | 1.6 ± 1.1 | 23 ± 15 | (2.6 ± 1.7)e23 | 1.59 ± 1.07 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-A | Cs-137 662 | 661.7 | 0.900 ± 0.062 | 10.0 ± 6.2 | 0.53 ± 0.34 | 0.083 ± 0.054 | 1.31 ± 0.85 | 4.3 ± 2.8 | 1.9 ± 1.2 | 27 ± 18 | (3.1 ± 2.0)e23 | 2.10 ± 1.36 |  |
| ORNEK-A | Co-60 1173 | 1173 | 0.931 ± 0.058 | 6.9 ± 5.8 | 0.36 ± 0.31 | 0.056 ± 0.049 | 1.9 ± 1.7 | 6.5 ± 5.7 | 2.8 ± 2.5 | 25 ± 22 | (2.8 ± 2.5)e23 | 1.95 ± 1.71 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-A | Co-60 1332 | 1332 | 0.934 ± 0.028 | 6.6 ± 2.8 | 0.34 ± 0.15 | 0.054 ± 0.024 | 2.03 ± 0.90 | 6.7 ± 3.0 | 2.9 ± 1.3 | 25 ± 11 | (2.9 ± 1.3)e23 | 2.01 ± 0.89 |  |
| ORNEK-B | Ba-133 81 | 80.9 | 0.090 ± 0.023 | 91.0 ± 2.3 | 12.0 ± 1.3 | 1.92 ± 0.21 | 0.0575 ± 0.0062 | 0.191 ± 0.021 | 0.0830 ± 0.0090 | 54.5 ± 5.9 | (5.94 ± 0.64)e23 | 2.27 ± 0.24 |  |
| ORNEK-B | Ba-133 303 | 295.4 | 0.744 ± 0.177 | 26 ± 18 | 1.5 ± 1.2 | 0.24 ± 0.19 | 0.47 ± 0.38 | 1.6 ± 1.3 | 0.67 ± 0.54 | 47 ± 38 | (5.1 ± 4.1)e23 | 2.75 ± 2.21 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-B | Ba-133 356 | 359.5 | 0.827 ± 0.066 | 17.3 ± 6.6 | 0.95 ± 0.40 | 0.151 ± 0.064 | 0.73 ± 0.31 | 2.4 ± 1.0 | 1.05 ± 0.45 | 35 ± 15 | (3.8 ± 1.6)e23 | 2.23 ± 0.94 |  |
| ORNEK-B | Cs-137 662 | 661.7 | 0.911 ± 0.070 | 8.9 ± 7.0 | 0.46 ± 0.38 | 0.074 ± 0.061 | 1.5 ± 1.2 | 5.0 ± 4.1 | 2.2 ± 1.8 | 25 ± 21 | (2.7 ± 2.2)e23 | 1.81 ± 1.50 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-B | Co-60 1173 | 1173 | 0.931 ± 0.033 | 6.9 ± 3.3 | 0.36 ± 0.18 | 0.057 ± 0.028 | 1.95 ± 0.97 | 6.5 ± 3.2 | 2.8 ± 1.4 | 26 ± 13 | (2.8 ± 1.4)e23 | 1.98 ± 0.99 |  |
| ORNEK-B | Co-60 1332 | 1332 | 0.932 ± 0.024 | 6.8 ± 2.4 | 0.35 ± 0.13 | 0.056 ± 0.021 | 1.97 ± 0.73 | 6.6 ± 2.4 | 2.8 ± 1.1 | 27 ± 10 | (3.0 ± 1.1)e23 | 2.10 ± 0.77 |  |


Veriden çıkarsanan kalınlık (kuramsal μ ile, tüm çizgilerin ağırlıklı ortalaması): ORNEK-A: 1.99 ± 0.13 mm; ORNEK-B: 2.24 ± 0.11 mm. Bu değer ölçülen kalınlıkla uyumlu olmalıdır (geometri/numune konumu kontrolü).


## 6. Kuramsal değerler (karışım kuralı, EPDL97)

| Numune | Cizgi | E_keV | MAC_kuram_cm2_g | LAC_kuram_cm-1 | HVL_kuram_cm | Zeff_kuram | Neff_kuram_e_g |
|---|---|---|---|---|---|---|---|
| ORNEK-A | Ba-133 81 | 80.9 | 0.8091 | 5.154 | 0.1345 | 33.28 | 3.771e+23 |
| ORNEK-A | Ba-133 303 | 295.4 | 0.1462 | 0.9312 | 0.7443 | 30.14 | 3.416e+23 |
| ORNEK-A | Ba-133 356 | 359.5 | 0.1213 | 0.7727 | 0.8971 | 28.6 | 3.241e+23 |
| ORNEK-A | Cs-137 662 | 661.7 | 0.07923 | 0.5047 | 1.373 | 26.2 | 2.968e+23 |
| ORNEK-A | Co-60 1173 | 1173 | 0.05729 | 0.3649 | 1.899 | 25.48 | 2.887e+23 |
| ORNEK-A | Co-60 1332 | 1332 | 0.05355 | 0.3411 | 2.032 | 25.42 | 2.88e+23 |
| ORNEK-B | Ba-133 81 | 80.9 | 1.688 | 10.6 | 0.06537 | 47.99 | 5.227e+23 |
| ORNEK-B | Ba-133 303 | 295.4 | 0.1715 | 1.077 | 0.6435 | 33.91 | 3.694e+23 |
| ORNEK-B | Ba-133 356 | 359.5 | 0.1358 | 0.8528 | 0.8128 | 31.46 | 3.427e+23 |
| ORNEK-B | Cs-137 662 | 661.7 | 0.08134 | 0.5108 | 1.357 | 27.45 | 2.99e+23 |
| ORNEK-B | Co-60 1173 | 1173 | 0.05711 | 0.3586 | 1.933 | 26.21 | 2.855e+23 |
| ORNEK-B | Co-60 1332 | 1332 | 0.05324 | 0.3344 | 2.073 | 26.11 | 2.844e+23 |


## 7. Uyarılar

- Spektrumlarda tespit edilemeyen çizgiler (analiz dışı bırakıldı): Am-241 59.5 (en yüksek 0.8σ); Co-57 122 (en yüksek 2.5σ)

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
