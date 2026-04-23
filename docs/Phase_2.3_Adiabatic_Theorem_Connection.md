# Faz 2.3 — Adiabatic Theorem Bağlantısı

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı

---

## İçerik Haritası

- **Bölüm A:** Adiabatic Quantum Computing (AQC) nedir?
- **Bölüm B:** Continuous'tan Discrete'e: Trotter Ayrıklaştırması
- **Bölüm C:** Adiabatic vs Variational: İki Rejim
- **Bölüm D:** $p \to \infty$ Teoremi (Farhi 2014)
- **Bölüm E:** Gap ve QAOA Performansı
- **Q&A İçgörüleri:** Üç kritik kavramın derinleştirilmesi

Faz 2.2'den elimizde: QAOA ansatz formülü $|\psi_p\rangle = U_B(\beta_p)U_C(\gamma_p)\cdots U_B(\beta_1)U_C(\gamma_1)|\psi_0\rangle$. Bu fazda ansatz'ın fiziksel temelini kuracağız.

---

# BÖLÜM A — Adiabatic Quantum Computing (AQC)

## A.1. Temel Fikir

AQC, gate-model'den **önce** gelen orijinal kuantum optimizasyon yaklaşımıdır (Farhi, Goldstone, Gutmann, Sipser 2000).

> Kolay bir Hamiltonian'ın ground state'inden başla. Hamiltonian'ı **yeterince yavaş** şekilde zor probleme dönüştür. Sistem yeni ground state'te (yani çözümde) kalır.

## A.2. Matematiksel Formülasyon

İki Hamiltonian:
- **$H_B$ (başlangıç):** Ground state'i kolay hazırlanabilir. QAOA için: $H_B = -\sum_i X_i$, ground state'i uniform superposition.
- **$H_C$ (hedef):** Ground state'i optimizasyon probleminin çözümü. QAOA için: $H_C = \frac{1}{2}\sum_{(i,j) \in E}(Z_i Z_j - \mathbb{1})$.

Zaman-bağımlı Hamiltonian:

$$H(s) = (1 - s) H_B + s H_C, \quad s = t/T \in [0, 1]$$

- $s = 0$: $H(0) = H_B$, sistem $|+\rangle^{\otimes n}$'de
- $s = 1$: $H(1) = H_C$, sistem ideal olarak $H_C$'nin ground state'inde

## A.3. Adiabatic Teoremi

Evrim zamanı $T$ yeterince büyükse:

$$T \gg \frac{\max_s \|\partial_s H(s)\|}{\min_s \Delta(s)^2}$$

burada $\Delta(s)$ = ground state ile ilk uyarılmış state arasındaki **enerji aralığı (gap)**, sistem başlangıç ground state'inden bitiş ground state'ine yüksek olasılıkla geçer.

**Kritik büyüklük:** gap $\Delta(s)$. Gap ne kadar küçükse, evrim o kadar yavaş olmalı.

## A.4. NP-Hard Problemlerin Tuzağı

NP-hard problemler için gap **exponential olarak küçülebilir**:

$$\Delta_{\min} \sim 2^{-n} \quad \Rightarrow \quad T \sim 4^n$$

Bu, AQC'nin NP-hard problemlerde klasik üstünlük **garantilemediğinin** matematiksel ifadesi.

---

# BÖLÜM B — Continuous'tan Discrete'e: Trotter Ayrıklaştırması

## B.1. Sorun

AQC sürekli zaman evrimi. Gate-based kuantum bilgisayarlar ayrık gate'lerle çalışır. Çözüm: **Trotter-Suzuki ayrıklaştırması.**

## B.2. Temel Problem

$H(s) = (1-s)H_B + sH_C$ için zaman evrimi:

$$U(T) = \mathcal{T} \exp\left(-i \int_0^T H(s(t)) \, dt\right)$$

Tek bir unitary olarak uygulanamaz çünkü $H_B$ ve $H_C$ **commute etmez**:

$$[H_B, H_C] \neq 0 \quad \text{(çünkü } [X, Z] = -2iY\text{)}$$

## B.3. Trotter Formülü

Kısa zaman adımı $\Delta t$ için:

$$e^{-i(A+B)\Delta t} \approx e^{-iA\Delta t} \cdot e^{-iB\Delta t} + O(\Delta t^2)$$

$p$ adıma bölersek:

$$U(T) \approx \prod_{k=1}^{p} e^{-iH_B \Delta t_k^{(B)}} \cdot e^{-iH_C \Delta t_k^{(C)}}$$

## B.4. QAOA Ansatz'ın Doğuşu

Parametrik yeniden adlandırma:
- $\beta_k := (1 - s_k)\Delta t$
- $\gamma_k := s_k \Delta t$

$$U_{\text{adiabatic}} \approx \prod_{k=1}^{p} e^{-i\beta_k H_B} \cdot e^{-i\gamma_k H_C} = \prod_{k=1}^{p} U_B(\beta_k) U_C(\gamma_k)$$

**Bu tam olarak QAOA ansatz'ıdır!**

## B.5. Önemli Sonuç

QAOA ansatz'ı gökten inmedi — **adiabatic evrimin doğal Trotter ayrıklaştırmasıdır**. Farhi 2014'ün yeniliği: $\gamma_k, \beta_k$ parametrelerini adiabatic schedule'a sabitlemek yerine **variational optimization** ile bulmak.

---

# BÖLÜM C — Adiabatic vs Variational: İki Rejim

## C.1. Rejim 1: Adiabatic Schedule (Pasif)

Parametreler adiabatic teoreminden türetilir:
- $\gamma_k = (k/p) \cdot \Delta t$
- $\beta_k = (1 - k/p) \cdot \Delta t$
- Toplam evrim zamanı $T = p \cdot \Delta t$

$p \to \infty$ ve $T$ yeterince büyük olduğunda optimal çözüme yakınsar. Ama çok büyük $p$ gerektirir → NISQ için uygun değil.

## C.2. Rejim 2: Variational (Aktif)

Parametreler optimize edilir:

$$(\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*) = \arg\min_{\boldsymbol{\gamma}, \boldsymbol{\beta}} \langle \psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) | H_C | \psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) \rangle$$

- Küçük $p$'de bile iyi approximation ratio sağlayabilir
- Farhi 2014: $p=1$ için 3-regular graflarda $r \geq 0.6924$ garantisi
- NISQ-uyumlu

## C.3. Karşılaştırma Tablosu

| Özellik | Adiabatic | Variational (QAOA) |
|---|---|---|
| Parametre kaynağı | Schedule'dan | Optimizer'dan |
| $p$ gereksinimi | Büyük | Küçük olabilir |
| Donanım uygunluğu | AQC özel donanım | NISQ gate-based |
| Performans garantisi | $p \to \infty$ limitinde | $p=1$ için alt sınır |
| Klasik postprocessing | Yok | Gerekli |

---

# BÖLÜM D — $p \to \infty$ Teoremi (Farhi 2014)

## D.1. Teoremin İfadesi

QAOA, $p \to \infty$ limitinde, optimal parametrelerle, **kesin optimal çözümü** bulur:

$$\lim_{p \to \infty} \max_{\boldsymbol{\gamma}, \boldsymbol{\beta}} \langle \psi_p | H_C | \psi_p \rangle = C^*$$

(Yol 2 konvansiyonu; Yol 1'de $\min \to -C^*$.)

## D.2. Ana Argüman

1. **Trotter yakınsaması:** $p$ büyüdükçe ayrıklaştırma hatası azalır
2. **Adiabatic limit:** Yeterince büyük $T$ ile adiabatic koşul sağlanır
3. **Ground state yakınsaması:** Sistem $H_C$'nin ground state'ine yakınsar

## D.3. Pratik Anlamı

- **Teorik:** QAOA her zaman optimal çözümü bulabilir (limit'te)
- **Pratik:** Küçük $p$ ile ne kadar iyi yapabiliriz?

Scaling deneylerimizin cevaplamaya çalıştığı soru: **N=3..10** için **p=1,2,3** değerlerinde approximation ratio nasıl davranır?

---

# BÖLÜM E — Gap ve QAOA Performansı

## E.1. Gap Scaling

Adiabatic teoriden $T \sim 1/\Delta_{\min}^2$. Küçük gap → yavaş evrim.

QAOA için etkisi:
- **Büyük gap (kolay problem):** Küçük $p$ yeterli
- **Küçük gap (zor problem):** Büyük $p$ gerekir

## E.2. MaxCut'ta Gap Varyasyonu

- **Dense graflar** (K_N): büyük gap, kolay
- **Sparse graflar** (3-regular): orta
- **Özel yapılı graflar**: zor olabilir

## E.3. Sunum Bağlantısı

Scaling deneylerinde:
1. Sabit $p$'de approximation ratio vs N
2. Sabit N'de approximation ratio vs $p$
3. Yorum: küçük $p$ nerelerde yeterli?

---

# Q&A İçgörüleri — Faz 2.3

## İçgörü 1: Gap Scaling'in QAOA'ya Etkisi

**Soru:** Gap exponential küçülürse $T$ nasıl scale eder? QAOA bu limitin altına inebilir mi?

**Cevap:** Gap $\Delta = 2^{-n}$ ise:

$$T \sim \frac{1}{\Delta_{\min}^2} \sim \frac{1}{(2^{-n})^2} = 4^n$$

**Exponential scaling.** Problem büyüdükçe adiabatic evrim zamanı exponential artar.

**QAOA bu limitin altına inemez, ama farklı trade-off yapabilir:**

| Senaryo | Gereksinim |
|---|---|
| Tam optimal çözüm | Aynı exponential tuzak ($p \to \infty$) |
| Yaklaşık optimal çözüm | Küçük $p$ yeterli olabilir (Farhi 2014 alt sınır) |

Bu, QAOA'nın "quantum speedup" iddiasının neden tartışmalı olduğunun sebebi. Klasik algoritmalar da yaklaşık çözüm üretebiliyor.

**Sunum bağlantısı:** NISQ karnesi slaytında QAOA'nın teorik sınırlamaları tartışılacak.

## İçgörü 2: $p \to \infty$ Teoreminin Pratik Değeri

**Soru:** Teorem neden pratik garanti değil?

**Cevap:** $p \to \infty$ demek **devre derinliği sonsuz** demek. Matematiksel olarak:

- Her gate'in hata oranı var → noise accumulation
- NISQ cihazları sınırlı coherence time (T1, T2)
- Belli bir derinlikten sonra kuantum durum dekohere olur

Teorem doğru, ama **fiziksel olarak erişilemeyen bir rejimi** tarif ediyor. Preskill 2018 (referans #4) tam bunu söylüyor: NISQ'te $p \leq 3$ civarında kalınmalı.

## İçgörü 3: Variational'ın Adiabatic'e Üstünlüğü — Derin Sebep

**Soru:** Variational optimizer küçük $p$'de nasıl iyi sonuç veriyor?

**Cevap — Üç katmanlı açıklama:**

### A. Parametre Esnekliği

Adiabatic schedule:
- $\gamma_k, \beta_k$ **monoton** değişir
- $\gamma$ artarken $\beta$ azalıyor, sabit hızla
- Her adım **küçük ve yumuşak**

Variational:
- $\gamma_k, \beta_k$ her katman için **bağımsız**
- Monoton olmak zorunda değil
- Her katman **büyük ve keskin** olabilir

### B. Hilbert Uzayında Kısayollar

**Adiabatic yol:** $H_B$ ground state'inden $H_C$ ground state'ine **sürekli ve yumuşak** bir yol. Ayrıklaştırmak çok adım gerektirir.

**Variational yol:** Aynı noktaları bağlayan ama **"keskin dönüşler"** ve **"kısayollar"** içeren bir yol. Optimizer bu kısayolları bulabilir.

**Analoji:** Adiabatic = A'dan B'ye sabit hızla düz çizgi. Variational = trafiği, eğimleri, tünelleri kullanan akıllı GPS. Aynı hedefe varır, ama variational daha az mesafe (küçük $p$) ile ulaşabilir.

### C. Gerçek Mekanizma — Quantum Interference

QAOA'nın performans kaynağı **kuantum girişimidir**:

1. $\gamma_1$ belli fazları yazar
2. $\beta_1$ bu fazları interfere ettirir
3. $\gamma_2, \beta_2$ interference örüntüsünü derinleştirir

Adiabatic schedule bu interference efektlerini **sömürmez** — sadece yavaş evrimle ground state'te kalmaya çalışır. Variational optimizer interference'ı **aktif kullanır**:

- İyi çözümlerde constructive interference
- Kötü çözümlerde destructive interference

### D. Neden $p=1$ Bile Yeterli Olabiliyor?

Farhi 2014 teoremi ($r \geq 0.6924$ for $p=1$, 3-regular graflar):

> Sadece tek bir cost+mixer katmanı, optimal $\gamma, \beta$ ile iyi interference yaratabiliyor.

Adiabatic'te $p=1$ neredeyse hiç evrim yok, hiçbir anlamlı ilerleme yok. Variational'de $p=1$ bile "en iyi single-step amplitude shift"i bulabilir.

**QAOA, Grover's amplitude amplification'ın problem-adaptif versiyonu gibi çalışır.** Grover sabit iterasyon (tek tip operatör), QAOA her katmanda farklı parametreler.

---

# Özet — Faz 2.3'ten Çıkan Eldeki Taşlar

1. ✅ AQC'nin temel fikri ve adiabatic teorem
2. ✅ Gap'in rolü: $T \sim 1/\Delta_{\min}^2$
3. ✅ NP-hard problemlerde exponential gap scaling tuzağı
4. ✅ Trotter-Suzuki ayrıklaştırması ile QAOA ansatz'ının türetilmesi
5. ✅ Adiabatic schedule vs variational optimization farkı
6. ✅ Farhi 2014 $p \to \infty$ teoremi ve NISQ sınırlaması
7. ✅ Variational'ın interference üzerinden kısayol bulma mekanizması
8. ✅ $p=1$'in bile neden anlamlı sonuç verebileceği

---

# Üç Kritik NISQ Sınırlaması (Sunum İçin)

Adiabatic ve teorik QAOA arasındaki fark NISQ'in üç temel sınırından kaynaklanır:

| Sınır | Etkisi |
|---|---|
| **Coherence time** | Derinlik $p$ sınırlı |
| **Gate error** | Noise accumulation $p$ ile büyür |
| **Measurement shots** | Expectation hesabı sınırlı örnekleme |

Bu üçü birlikte, neden $p \in \{1,2,3\}$ rejiminde çalışmak zorunda olduğumuzu açıklar.

---

# Sırada: Faz 2.4 — Ölçüm ve Approximation Ratio

- Computational basis ölçümü ve bitstring sampling
- Expectation value $\langle \psi | H_C | \psi \rangle$ nasıl tahmin edilir
- Shot noise ve variance
- Approximation ratio tanımı ve yorumu
- Dejenerasyon: birden fazla optimal bitstring'in ölçüm dağılımına yansıması
