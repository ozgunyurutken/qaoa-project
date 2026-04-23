# Faz 2.4 — Ölçüm ve Approximation Ratio

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı

---

## İçerik Haritası

- **Bölüm A:** Computational basis ölçümü
- **Bölüm B:** Expectation value tahmini (statevector vs sampling)
- **Bölüm C:** Approximation ratio tanımı ve referans değerler
- **Bölüm D:** Dejenerasyon ve ölçüm dağılımı
- **Bölüm E:** Ölçümden klasik çözüme geri dönüş
- **Q&A İçgörüleri:** Üç kritik kavram

Faz 2.3'ten: QAOA ansatz'ı adiabatic Trotter ayrıklaştırması. Bu fazda algoritmanın "kapanışını" yapıyoruz — ölçüm ve sonuç yorumu.

---

# BÖLÜM A — Computational Basis Ölçümü

## A.1. Ne Ölçüyoruz?

MaxCut için çıktı **bitstring** olmalı (hangi düğüm hangi kümede). Bunu **computational basis ölçümü** ile elde ederiz — her qubit'i $Z$ baz'ında ölçeriz.

Hocanın QDW3 measurement postulate:

> "Bir observable'ın ölçümü yapıldığında, kuantum durum ölçüm operatörünün bir eigenvector'üne çöker ve karşılık gelen eigenvalue gözlemlenir."

$Z$ operatörünün eigenvector'leri $|0\rangle$ ve $|1\rangle$. $n$ qubit'i $Z$ baz'ında ölçmek = her qubit için 0 veya 1 = bir **bitstring**.

## A.2. Matematiksel Formalizm

Optimal parametrelerle hazırlanan QAOA durumu:

$$|\psi_p(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*)\rangle = \sum_{z \in \{0,1\}^n} c_z |z\rangle$$

Born kuralı:

$$P(z) = |c_z|^2 = |\langle z | \psi_p \rangle|^2$$

**Önemli:** QAOA'nın başarısı, $|c_z|^2$'nin optimal bitstring'lerde yoğunlaşmasıdır.

## A.3. K₃ Örneğiyle Somut Bağlantı

K₃ için 6 optimal bitstring (cost = 2): $|001\rangle, |010\rangle, |011\rangle, |100\rangle, |101\rangle, |110\rangle$.

İdeal optimize edilmiş QAOA durumu:

$$|\psi_1(\gamma^*, \beta^*)\rangle \approx \frac{1}{\sqrt{6}} \sum_{z \in \text{optimal}} e^{i\phi_z} |z\rangle$$

Ölçümde her optimal bitstring $\sim 1/6$, $|000\rangle$ ve $|111\rangle$ $\sim 0$.

---

# BÖLÜM B — Expectation Value Tahmini

## B.1. Neden Tek Ölçüm Yetmez?

QAOA'nın optimize ettiği:

$$F_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) = \langle \psi_p | H_C | \psi_p \rangle$$

Tek ölçüm bir bitstring verir — örneklem, ortalama değil.

Hocanın QDW3 tanımı:

$$\langle A \rangle = \langle \psi | A | \psi \rangle = \sum_i a_i P(a_i)$$

QAOA bağlamında (Yol 1):

$$\langle H_C \rangle = \sum_z (-C(z)) \cdot P(z)$$

## B.2. Shot-Based Tahmin (Gerçek Donanım)

1. Devreyi hazırla: $|\psi_p\rangle$
2. Ölçüm yap, bitstring $z^{(1)}$ al
3. Devreyi yeniden hazırla
4. $N_{\text{shots}}$ kez tekrarla
5. Tahmin:

$$\widehat{\langle H_C \rangle} = \frac{1}{N_{\text{shots}}} \sum_{k=1}^{N_{\text{shots}}} (-C(z^{(k)}))$$

## B.3. Shot Noise

$$\text{std}\left[\widehat{\langle H_C \rangle}\right] = \frac{\sigma(H_C)}{\sqrt{N_{\text{shots}}}}$$

- $N_{\text{shots}} = 1024$: tipik pratik değer
- $N_{\text{shots}} = 10000$: hassas hesaplamalar
- Exact simulation: analytic hesap

## B.4. Statevector vs Sampling

Bizim simülasyonlarımızda:

| Mod | Yöntem | Shot noise | Bilgi |
|---|---|---|---|
| **Statevector** | Tüm $\psi$ vektörü, analitik $\langle H_C \rangle$ | Yok | Tam |
| **Sampling** | Gerçek donanım simülasyonu | Var | Sınırlı |

N≤10 için statevector mümkün ve önerilen. Bizim scope'ta statevector kullanıyoruz.

---

# BÖLÜM C — Approximation Ratio

## C.1. Standart Tanım

$$r = \frac{\text{beklenen cost}}{\text{optimal cost}} = \frac{\langle C \rangle}{C^*}$$

Yol 1 konvansiyonunda:

$$r = \frac{-\langle H_C \rangle}{C^*}$$

**Yorum:**
- $r = 1$: mükemmel
- $r = 0$: berbat
- $r \in [0, 1]$: genel

## C.2. K₃ İçin Referans Değerler

| Durum | Beklenen cost | $r$ |
|---|---|---|
| Uniform superposition | $1.5$ | $0.75$ |
| Optimal QAOA p=1 | ~$1.73$ | ~$0.866$ |
| Optimal QAOA p=2 | ~$1.96$ | ~$0.98$ |
| Tam optimal | $2$ | $1.0$ |

(Yaklaşık değerler; tam sayılar Faz 4'te.)

## C.3. Farhi 2014 Alt Sınırı

**Teorem:** Herhangi bir 3-regular graf için, $p=1$ QAOA'nın optimal $\gamma^*, \beta^*$ ile:

$$r \geq 0.6924$$

**Önem:**
- **Her** 3-regular graf için (graf-bağımsız)
- **Her $n$** için (boyut-bağımsız)
- Sadece $p=1$ — en sığ QAOA bile anlamlı
- İlk rigorous NISQ performans garantisi

## C.4. Klasik Üst Sınır: Goemans-Williamson

**Goemans-Williamson (1995):**
- Semidefinite programming (SDP) tabanlı
- $r \geq 0.878$ garanti
- Unique Games Conjecture doğruysa polinomiyal zamanda **en iyi** klasik algoritma

**QAOA p=1 vs GW:**
- QAOA p=1: $\geq 0.6924$
- GW: $\geq 0.878$

QAOA p=1 garantisi GW'den zayıf. Ama bu hikâyenin tamamı değil (Q&A İçgörü 3'te detay).

---

# BÖLÜM D — Dejenerasyon ve Ölçüm Dağılımı

## D.1. K₃ Dejenerasyonu

K₃: 6 optimal bitstring (eigenvalue $= -2$, 6-kat dejenere).

**QAOA bunları ayırt etmez, ayırt etmesine gerek yok.** Olasılık kütlesi 6 optimal arasında paylaşılır. Her ölçümde 6'sından biri gelir — hepsi aynı cut size.

## D.2. İdeal Histogram

```
Probability
   |
0.17|   ▓  ▓  ▓  ▓  ▓  ▓
   |   ▓  ▓  ▓  ▓  ▓  ▓
0.00|▁  ▓  ▓  ▓  ▓  ▓  ▓  ▁
    |000 001 010 011 100 101 110 111
```

## D.3. $\mathbb{Z}_2$ Simetri Koruması

K₃'ün global spin-flip simetrisi: $\mathbf{s} \to -\mathbf{s}$ cost'u değiştirmez. QAOA ansatz'ı bu simetriyi otomatik korur ($H_B$ ve $H_C$ simetri altında değişmez).

Sonuç: $P(|z\rangle) = P(|\bar{z}\rangle)$
- $P(|001\rangle) = P(|110\rangle)$
- $P(|010\rangle) = P(|101\rangle)$
- $P(|011\rangle) = P(|100\rangle)$
- $P(|000\rangle) = P(|111\rangle)$

Sunumda histogram slaytında 3 eş çift görünecek.

---

# BÖLÜM E — Ölçümden Klasik Çözüme

## E.1. Tam I/O Döngüsü

```
1. Klasik graf G = (V, E)
       ↓ (encoding)
2. Ising Hamiltonian H_C
       ↓ (circuit construction)
3. QAOA devresi (p-layer ansatz)
       ↓ (classical optimization)
4. Optimal parametreler (γ*, β*)
       ↓ (measurement, N_shots)
5. Bitstring histogramı
       ↓ (decoding)
6. En iyi bitstring(ler) → klasik cut S ⊆ V
```

## E.2. En İyi Bitstring Seçimi

**Yaklaşım 1: En yüksek olasılıklı.** Most frequent bitstring. Basit, sub-optimal.

**Yaklaşım 2: Post-selection.** Her gözlemlenen bitstring için klasik cost hesapla, en yüksek olanı seç:

$$z^* = \arg\max_{z \in \text{observed}} C(z)$$

Daha iyi performans.

**Yaklaşım 3: Post-processing.** QAOA sonucu klasik lokal arama (bit-flip hill climbing) ile iyileştirilir. "Warm-start."

**Bizim seçimimiz:** Yaklaşım 2 (post-selection).

## E.3. Sunum İçin I/O Diyagramı

Faz 1'de planladığımız "I/O Encoding & Measurement Extraction" diyagramı tam bu döngüyü gösterecek.

---

# Q&A İçgörüleri — Faz 2.4

## İçgörü 1: Kapsam Disiplini (Statevector Only)

**Soru:** NISQ karnesinde shot noise tartışacağız ama kendi deneylerimizde statevector kullanıyoruz. Bu tutarsız mı?

**Cevap:** Tutarsız değil, **pedagojik olarak iki farklı içerik**:

**Faz 1'de kesinleştirilen scope:**
- Statevector simülasyonu
- N=3..10 (opsiyonel 11,12)
- p=1,2,3
- 3-regular graflar
- **Gerçek donanım testi YOK**
- **Gürültülü simülasyon YOK**

**Sunumda iki amaç:**

| İçerik | Amaç |
|---|---|
| Bizim deneylerimiz (statevector) | Algoritmayı anlatmak, exact metrikler |
| NISQ karnesi slaytı (kavramsal) | Bağlam vermek, literatürden |

İki içerik birlikte dengeli bir sunum yapar:
- Exact sonuçlar → "algoritma ne yapıyor, gerçekten yapıyor"
- NISQ kavramsal → "gerçek donanımda karşılaşılacak problemler"

**Kapsam disiplini neden önemli?**
1. Hoca "complex code" istemiyor
2. Zaman bütçesi (23 Nisan teslim)
3. Sunum odağı algoritma mekaniği

## İçgörü 2: Dejenerasyon Feature, Not a Bug

**Soru:** K₃'te 6 optimal bitstring'den hangisi gelir bilinmiyor. Bu sorun değil mi?

**Cevap:** Sorun değil, çünkü hepsi global optimum. MaxCut bize bir cut istiyor, hangi cut olduğu önemli değil.

**Pedagojik framing:** QAOA'nın superposition'ı tüm eşdeğer çözümleri aynı anda içeriyor, ölçüm bir tanesini seçiyor. Bu "kuantum paralellik" sezgisinin somut örneği.

Sunumda histogram slaytında 6 eş tepe → "dejenerasyon + $\mathbb{Z}_2$ simetrisi" bağlantısı → "Explicit Demo (20 puan)" kriterine derinlik.

## İçgörü 3: Farhi 2014'ün Üçlü Teorik Değeri

**Soru:** GW $r \geq 0.878$ verirken QAOA p=1 $r \geq 0.6924$ veriyor. Farhi 2014'ün değeri nedir?

**Cevap — Üç katmanlı:**

### A. İlk Rigorous NISQ Sonucu

Farhi 2014 kuantum optimizasyon tarihinde **ilk kez** şunu gösterdi:
- Bir kuantum algoritması (QAOA)
- Belirli bir problem sınıfı için (3-regular MaxCut)
- **Her instance'ta** (graf-bağımsız)
- **Her boyutta** (qubit-bağımsız)
- **Sabit p'de** (p=1, derinlik minimal)
- Rigorous alt sınırı kanıtlanmış performans

Öncesinde kuantum optimizasyon için sadece **adiabatic heuristic** vardı — "çalışır umuyoruz, ama kanıt yok."

### B. Quantum Supremacy Sampling (Farhi-Harrow 2016)

**Farhi-Harrow 2016** ("Quantum supremacy through QAOA", arXiv:1602.07674):

> QAOA p=1 çıktı dağılımı **klasik olarak verimli simüle edilemez** (yaygın kompleksite varsayımları altında).

Yani:
- Approximation ratio olarak GW'den zayıf olsa bile
- **Sampling** açısından QAOA klasiğin yapamadığını yapıyor
- Quantum speedup iddiası sampling üzerinden

### C. Açık Araştırma Problemi

QAOA'nın GW'u **genel olarak geçmesi bilinmiyor**. Özel durumlarda geçildiği gösterildi, ama universal üstünlük yok.

**Ekleme — ileride:** $p$ artırıldıkça approximation ratio iyileşir. Pratik sınır NISQ donanım kalitesinden geliyor. Donanım iyileşirse daha yüksek p → daha iyi ratio.

### Sunum Bağlantısı

Farhi 2014'e atıf yaparken üç noktayı vurgulayacağız:
1. İlk kanıtlanmış alt sınır
2. İlk NISQ-uyumlu performans garantisi
3. Açık problem: klasik üstünlük nerede/nasıl?

Hocanın Hafta 13 konusuyla ("Current Research on Quantum Algorithms") doğrudan örtüşür.

---

# Özet — Faz 2.4'ten Çıkan Eldeki Taşlar

1. ✅ Computational basis ölçümü, Born kuralı, bitstring sampling
2. ✅ Expectation value tahmini, shot noise formülü
3. ✅ Statevector vs sampling karşılaştırması (bizim scope: statevector)
4. ✅ Approximation ratio tanımı ve K₃ referans değerleri
5. ✅ Farhi 2014 alt sınırı + Goemans-Williamson karşılaştırması
6. ✅ Dejenerasyon ve $\mathbb{Z}_2$ simetri koruması
7. ✅ Ölçümden klasik çözüme post-selection yaklaşımı
8. ✅ Kapsam disiplini konfirmasyonu (statevector only)
9. ✅ Farhi 2014'ün teorik değeri (ilk rigorous NISQ sonucu + sampling supremacy + açık problem)

---

# Sırada: Faz 2.5 — Variational Döngü ve Klasik Optimizasyon

- Hybrid quantum-classical yapı (detaylı)
- Klasik optimizer seçimleri (COBYLA, SPSA, L-BFGS-B)
- Parametre uzayı yapısı ve barren plateau kavramsal
- Initialization stratejileri (random, adiabatic-inspired, parameter concentration)
- Convergence ve local minima
