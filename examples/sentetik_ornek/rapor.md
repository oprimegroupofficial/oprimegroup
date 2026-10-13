# SENTETIK ORNEK - GERCEK VERI DEGILDIR (yalnizca cikti bicimini gostermek icin)

## 1. Durum

- Spektrum sayısı: 3 (numune: 2, numunesiz/I0: var)
- Kalınlık girilmiş mi: evet; yoğunluk: evet; bileşim: evet

## 2. Veri kontrolü ve kalibrasyon

| Spektrum | Toplam_sayim | Canli_sure_s | Gercek_sure_s | Olu_zaman_yuzde | Sayim_hizi_cps | RMS_artik_keV | Cozunurluk_FWHM_662_yuzde |
|---|---|---|---|---|---|---|---|
| Bos (I0) | 2788065 | 7200 | 7380 | 2.439 | 387.2 | 0.2203 | 7.075 |
| ORNEK-A | 2734556 | 7200 | 7380 | 2.439 | 379.8 | 0.1602 | 6.997 |
| ORNEK-B | 2722886 | 7200 | 7380 | 2.439 | 378.2 | 0.04781 | 7.001 |

- Bos (I0): `E[keV] = -0.471082 + 0.501416*ch^1 + 1.30397e-05*ch^2`
- ORNEK-A: `E[keV] = -0.212672 + 0.50142*ch^1 + 1.30318e-05*ch^2`
- ORNEK-B: `E[keV] = -0.155598 + 0.501027*ch^1 + 1.3217e-05*ch^2`

## 3. Tespit edilen çizgiler (net alan, istatistik belirsizlik)

| Spektrum | Cizgi | E_nominal_keV | Alan ± u | Anlamlilik_sigma | FWHM_yuzde | chi2_ndf | Kabul_varyant |
|---|---|---|---|---|---|---|---|
| Bos (I0) | Ba-133 81 | 80.9 | 30422 ± 733 | 41.52 | 13.63 | 0.8359 | 6 |
| Bos (I0) | Ba-133 303 | 295.4 | 19132 ± 1065 | 17.96 | 9.319 | 0.9794 | 7 |
| Bos (I0) | Ba-133 356 | 359.5 | 48970 ± 1222 | 40.08 | 8.479 | 0.9794 | 7 |
| Bos (I0) | Cs-137 662 | 661.7 | 42198 ± 1000 | 42.2 | 7.198 | 1.117 | 7 |
| Bos (I0) | Co-60 1173 | 1173 | 146820 ± 1675 | 87.63 | 5.85 | 0.9953 | 8 |
| Bos (I0) | Co-60 1332 | 1332 | 146663 ± 1168 | 125.5 | 5.558 | 0.9953 | 8 |
| ORNEK-A | Ba-133 81 | 80.9 | 10150 ± 568 | 17.88 | 13.32 | 0.8197 | 6 |
| ORNEK-A | Ba-133 303 | 295.4 | 16525 ± 1061 | 15.57 | 9.094 | 1.039 | 7 |
| ORNEK-A | Ba-133 356 | 359.5 | 43170 ± 1266 | 34.09 | 8.609 | 1.039 | 7 |
| ORNEK-A | Cs-137 662 | 661.7 | 37721 ± 890 | 42.38 | 6.923 | 0.8758 | 7 |
| ORNEK-A | Co-60 1173 | 1173 | 137193 ± 1757 | 78.07 | 5.871 | 1.064 | 8 |
| ORNEK-A | Co-60 1332 | 1332 | 137401 ± 1223 | 112.4 | 5.58 | 1.064 | 8 |
| ORNEK-B | Ba-133 81 | 80.9 | 2815 ± 332 | 8.482 | 9.623 | 1.066 | 6 |
| ORNEK-B | Ba-133 303 | 295.4 | 14123 ± 1006 | 14.03 | 8.828 | 0.9639 | 7 |
| ORNEK-B | Ba-133 356 | 359.5 | 40362 ± 1172 | 34.43 | 8.257 | 0.9639 | 7 |
| ORNEK-B | Cs-137 662 | 661.7 | 38223 ± 961 | 39.76 | 7.149 | 1.067 | 7 |
| ORNEK-B | Co-60 1173 | 1173 | 137199 ± 1683 | 81.52 | 5.912 | 0.965 | 8 |
| ORNEK-B | Co-60 1332 | 1332 | 137152 ± 1178 | 116.4 | 5.629 | 0.965 | 8 |


## 4. Göreli zayıflama (bilgi amaçlı)

Referans: **numunesiz ölçüm (I0)**. T = I/I0; ±: istatistik ⊕ model (kalınlık/yoğunluk belirsizliği hariç).

| Numune | Cizgi | E_keV | T=I/Iref | u_T | Anlamlilik_sigma |
|---|---|---|---|---|---|
| ORNEK-A | Ba-133 81 | 80.9 | 0.3336 | 0.02223 | 16.48 |
| ORNEK-A | Ba-133 303 | 295.4 | 0.8637 | 0.08623 | 1.467 |
| ORNEK-A | Ba-133 356 | 359.5 | 0.8816 | 0.03646 | 3.048 |
| ORNEK-A | Cs-137 662 | 661.7 | 0.8939 | 0.03103 | 3.231 |
| ORNEK-A | Co-60 1173 | 1173 | 0.9344 | 0.02943 | 2.153 |
| ORNEK-A | Co-60 1332 | 1332 | 0.9368 | 0.01426 | 4.286 |
| ORNEK-B | Ba-133 81 | 80.9 | 0.09254 | 0.01203 | 18.3 |
| ORNEK-B | Ba-133 303 | 295.4 | 0.7382 | 0.09265 | 2.419 |
| ORNEK-B | Ba-133 356 | 359.5 | 0.8242 | 0.03359 | 4.743 |
| ORNEK-B | Cs-137 662 | 661.7 | 0.9058 | 0.03561 | 2.516 |
| ORNEK-B | Co-60 1173 | 1173 | 0.9345 | 0.0167 | 3.792 |
| ORNEK-B | Co-60 1332 | 1332 | 0.9352 | 0.01212 | 5.173 |


## 5. Sonuçlar

Tablo değerleri k = 2 kapsam katsayısıyla verilmiştir.

| Numune | Çizgi | E (keV) | T = I/I0 | RPE (%) | LAC μ (cm⁻¹) | MAC μ/ρ (cm²/g) | HVL (cm) | TVL (cm) | MFP (cm) | Zeff | Neff (e/g) | Çıkarsanan kalınlık (mm) | Not |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ORNEK-A | Ba-133 81 | 80.9 | 0.334 ± 0.044 | 66.6 ± 4.4 | 5.49 ± 0.67 | 0.86 ± 0.11 | 0.126 ± 0.015 | 0.420 ± 0.051 | 0.182 ± 0.022 | 35.4 ± 4.3 | (4.02 ± 0.49)e23 | 2.13 ± 0.26 |  |
| ORNEK-A | Ba-133 303 | 295.4 | 0.864 ± 0.172 | 14 ± 17 | 0.73 ± 1.00 | 0.11 ± 0.16 | 0.9 ± 1.3 | 3.1 ± 4.3 | 1.4 ± 1.9 | 24 ± 32 | (2.7 ± 3.7)e23 | 1.57 ± 2.14 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-A | Ba-133 356 | 359.5 | 0.882 ± 0.073 | 11.8 ± 7.3 | 0.63 ± 0.41 | 0.099 ± 0.065 | 1.10 ± 0.72 | 3.7 ± 2.4 | 1.6 ± 1.0 | 23 ± 15 | (2.6 ± 1.7)e23 | 1.63 ± 1.07 |  |
| ORNEK-A | Cs-137 662 | 661.7 | 0.894 ± 0.062 | 10.6 ± 6.2 | 0.56 ± 0.35 | 0.088 ± 0.054 | 1.24 ± 0.77 | 4.1 ± 2.5 | 1.8 ± 1.1 | 29 ± 18 | (3.3 ± 2.0)e23 | 2.22 ± 1.38 |  |
| ORNEK-A | Co-60 1173 | 1173 | 0.934 ± 0.059 | 6.6 ± 5.9 | 0.34 ± 0.31 | 0.053 ± 0.049 | 2.0 ± 1.9 | 6.8 ± 6.3 | 2.9 ± 2.7 | 24 ± 22 | (2.7 ± 2.5)e23 | 1.86 ± 1.73 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-A | Co-60 1332 | 1332 | 0.937 ± 0.029 | 6.3 ± 2.9 | 0.33 ± 0.15 | 0.051 ± 0.024 | 2.13 ± 0.99 | 7.1 ± 3.3 | 3.1 ± 1.4 | 24 ± 11 | (2.8 ± 1.3)e23 | 1.91 ± 0.89 |  |
| ORNEK-B | Ba-133 81 | 80.9 | 0.093 ± 0.024 | 90.7 ± 2.4 | 11.9 ± 1.3 | 1.89 ± 0.21 | 0.0582 ± 0.0064 | 0.193 ± 0.021 | 0.0840 ± 0.0092 | 53.9 ± 5.9 | (5.87 ± 0.64)e23 | 2.24 ± 0.25 |  |
| ORNEK-B | Ba-133 303 | 295.4 | 0.738 ± 0.185 | 26 ± 19 | 1.5 ± 1.3 | 0.24 ± 0.20 | 0.46 ± 0.38 | 1.5 ± 1.3 | 0.66 ± 0.54 | 48 ± 40 | (5.2 ± 4.3)e23 | 2.82 ± 2.33 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-B | Ba-133 356 | 359.5 | 0.824 ± 0.067 | 17.6 ± 6.7 | 0.97 ± 0.41 | 0.154 ± 0.065 | 0.72 ± 0.30 | 2.4 ± 1.0 | 1.03 ± 0.44 | 36 ± 15 | (3.9 ± 1.6)e23 | 2.27 ± 0.96 |  |
| ORNEK-B | Cs-137 662 | 661.7 | 0.906 ± 0.071 | 9.4 ± 7.1 | 0.49 ± 0.39 | 0.079 ± 0.063 | 1.4 ± 1.1 | 4.7 ± 3.7 | 2.0 ± 1.6 | 27 ± 21 | (2.9 ± 2.3)e23 | 1.94 ± 1.54 | LAC < 3σ: HVL/TVL/MFP güvenilir değil |
| ORNEK-B | Co-60 1173 | 1173 | 0.934 ± 0.033 | 6.6 ± 3.3 | 0.34 ± 0.18 | 0.054 ± 0.028 | 2.0 ± 1.1 | 6.8 ± 3.6 | 3.0 ± 1.6 | 25 ± 13 | (2.7 ± 1.4)e23 | 1.89 ± 1.00 |  |
| ORNEK-B | Co-60 1332 | 1332 | 0.935 ± 0.024 | 6.5 ± 2.4 | 0.34 ± 0.13 | 0.053 ± 0.021 | 2.07 ± 0.80 | 6.9 ± 2.7 | 3.0 ± 1.2 | 26 ± 10 | (2.9 ± 1.1)e23 | 2.01 ± 0.78 |  |


Veriden çıkarsanan kalınlık (kuramsal μ ile, tüm çizgilerin ağırlıklı ortalaması): ORNEK-A: 1.86 ± 0.28 mm; ORNEK-B: 2.07 ± 0.24 mm. Bu değer ölçülen kalınlıkla uyumlu olmalıdır (geometri/numune konumu kontrolü).


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

- Spektrumlarda tespit edilemeyen çizgiler (analiz dışı bırakıldı): Co-57 122 (en yüksek 2.5σ)

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
