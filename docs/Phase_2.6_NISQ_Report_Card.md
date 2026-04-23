# Faz 2.6 — NISQ Karnesi ve Kritik Performans Sınırları

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı

---

## İçerik Haritası

- **Bölüm A:** NISQ nedir, QAOA neden NISQ-uyumlu?
- **Bölüm B:** QAOA'nın NISQ avantajları (4 madde)
- **Bölüm C:** QAOA'nın NISQ zorlukları (5 madde)
- **Bölüm D:** Fault-Tolerant vs NISQ karşılaştırması
- **Bölüm E:** Quantum advantage tartışması
- **Bölüm F:** Sunum için NISQ karnesi formatı (Slayt 10 taslağı)
- **Q&A İçgörüleri:** Üç kritik kavram

Faz 2.5'ten: variational döngü ve klasik optimizasyon. Bu faz sunumun "Complexity & Resource Analysis (15p)" kriterine doğrudan hizmet ediyor.

---

# BÖLÜM A — NISQ Nedir?

## A.1. Preskill'in Tanımı

**Preskill 2018:** Noisy Intermediate-Scale Quantum
- **Noisy:** Gate'ler mükemmel değil
- **Intermediate-Scale:** 50-1000 qubit
- **Quantum:** Klasik simülasyon sınırlarını aşan hesaplamalar mümkün

NISQ cihazlar **FTQC değil** — hata düzeltme yok, ham fiziksel qubit'ler.

## A.2. NISQ'in Üç Temel Sınırlaması

**1. Coherence time (T1, T2):** Kuantum durumun yaşam süresi. Devre derinliği sınırı.

**2. Gate error:** Her gate hata ekler. Çarpımsal birikim:
$$P_{\text{success}} \sim (1-\epsilon)^{\text{gate count}}$$

**3. Measurement shots:** Expectation için $N_{\text{shots}}$ ölçüm, shot noise $\sim 1/\sqrt{N_{\text{shots}}}$.

## A.3. Neden QAOA NISQ-Uyumlu?

- Kısa devre derinliği (küçük $p$)
- Variational yapı → noise toleransı
- Hybrid quantum-classical → klasik kısım "temiz"
- Problem-spesifik → sığ

---

# BÖLÜM B — QAOA'nın NISQ Avantajları

## B.1. Avantaj 1: Lineer Derinlik Scaling

$$D_{\text{QAOA}} = 3p$$

$p \in \{1,2,3\}$ → derinlik $\leq 9$, bugünkü NISQ donanımlarına uygun.

## B.2. Avantaj 2: Sparse Connectivity

QAOA cost operator graf yapısını takip eder. 3-regular: her qubit 3 komşusuyla etkileşir.
- Gerçek donanımda lokal gate yeterli
- Uzun-mesafe SWAP chain gerekmeyebilir
- Hardware-native mapping mümkün

VQE chemistry Hamiltonians'ı all-to-all → expensive SWAP. QAOA bu problemden kaçınır.

## B.3. Avantaj 3: Variational Noise Tolerance

Variational algoritmalar noise'a kısmi dayanıklı:
- Optimizer noisy function'ı minimize eder
- "Noisy hardware'de en iyi" çözüme gider
- Bir tür error mitigation

## B.4. Avantaj 4: Küçük Parametre Sayısı

| Algoritma | Parametre |
|---|---|
| QAOA p=3 | 6 |
| VQE UCCSD | $O(n^4)$ |
| Quantum NN | $O(n \cdot L)$ |

Küçük uzay → hızlı klasik optimizasyon → daha az devre → donanım süresi tasarrufu.

---

# BÖLÜM C — QAOA'nın NISQ Zorlukları

## C.1. Zorluk 1: Barren Plateau

Faz 2.5.E'den: gradient'lerin exponential küçülmesi.

**QAOA'da:**
- Küçük $p$ riski azaltır
- Büyük $n$ + büyük $p$ riskli
- Smart init kritik

**Bizim scope'ta düşük risk** (N≤10, p≤3).

## C.2. Zorluk 2: Ölçüm Bütçesi

Tipik senaryo:
- 1 iterasyon = 1000 shots
- Optimizasyon = 100 iter = 100,000 shots
- Bir graf ~ 10 saniye donanım süresi
- 10 graf = 100 saniye + queue

**Sonuç:** Gerçek donanım pahalı. Bizim statevector yaklaşımı bu yükü bypass ediyor.

## C.3. Zorluk 3: Klasik Optimizer Darboğazı

- Her iterasyon ayrı devre
- Klasik ↔ kuantum iletişim latency
- Cloud queue → saatler sürebilir

**Çözümler:**
- Batch execution
- Sessions (IBM Quantum)
- On-premise hardware

## C.4. Zorluk 4: Noise Accumulation

CNOT sayısı $= 2p|E|$. N=10, 3-regular ($|E|=15$), p=3 → 90 CNOT. $\epsilon=0.01$ için $(0.99)^{90} \approx 0.40$.

**Küçük bütçe senaryosu:** N=6, p=2, 3-regular → 36 CNOT → $(0.99)^{36} \approx 0.70$. Scope'umuzun küçük ucunda gerçek donanım bile ulaşılabilir rejimde.

**Error mitigation (scope dışı):**
- Zero-noise extrapolation
- Probabilistic error cancellation
- Symmetry verification

## C.5. Zorluk 5: Hardware Connectivity

NISQ donanımları all-to-all değil. Graf topolojisi ↔ hardware topolojisi uyumsuzluğu → SWAP chain → derinlik artar → noise artar.

**Çözümler:**
- Graph-aware compilation (Qiskit transpiler)
- Problem-hardware matching
- Hardware-efficient ansatz

Bizim scope'ta (statevector) bu problem yok.

---

# BÖLÜM D — Fault-Tolerant vs NISQ

## D.1. FTQC

- Quantum error correction kodları
- Arbitrary devre derinliği
- Overhead: 1000:1 veya daha fazla
- Milyonlarca qubit gerekir
- 2030+ tahmini

**FTQC algoritmaları:**
- Shor (factoring) — exponential speedup kanıtlı
- HHL (linear systems) — exponential speedup kanıtlı
- Grover (search) — quadratic speedup kanıtlı
- Quantum Phase Estimation

## D.2. NISQ

- Hata düzeltme yok
- Derinlik sınırlı (~100 gate practical)
- 100-1000 fiziksel qubit
- Bugün mevcut (2024-2025)
- Variational algoritmalar

## D.3. QAOA Hangi Rejimde?

**Her ikisinde de geçerli:**
- NISQ'te: sığ $p$, heuristik, yaklaşık
- FTQC'de: büyük $p$, adiabatic limit, optimal

**Bu nadir özellik** — QAOA sürdürülebilir algoritma, donanım evrimi kapsamını genişletiyor.

---

# BÖLÜM E — Quantum Advantage Tartışması

## E.1. Üç İddia Türü

**1. Approximation ratio advantage:** QAOA > klasik?
*Durum:* Genel olarak hayır. Goemans-Williamson $\geq 0.878$, QAOA p=1 $\geq 0.6924$. Özel graflar için QAOA daha iyi olabilir, universal üstünlük yok.

**2. Time complexity advantage:** QAOA daha hızlı?
*Durum:* Tartışmalı. Gerçek donanım overhead'i (queue, shots) dahil QAOA bugün pratik olarak daha yavaş.

**3. Sampling advantage (Farhi-Harrow 2016):** QAOA dağılımı klasik simüle edilemez?
*Durum:* Hayır (varsayımsal). Ama sampling advantage ≠ optimization advantage.

## E.2. Sunum İçin Dürüst Denge

- QAOA teorik olarak ilginç, pratik avantajı belirsiz
- Farhi 2014 rigorous alt sınırı önemli adım
- NISQ uyumluluğu pratik değer
- Universal speedup yok, aktif araştırma

Hocanın Hafta 13 "Current Research on Quantum Algorithms" konusuyla örtüşür.

---

# BÖLÜM F — Slayt 10 Taslağı: QAOA NISQ Report Card

**Başlık:** QAOA on NISQ: A Report Card

**İki sütunlu yapı:**

**Sütun 1 — Avantajlar (yeşil tonlar):**
| Özellik | Neden önemli |
|---|---|
| Shallow depth | Coherence time sınırı karşılanır |
| Variational loop | Noise tolerance |
| Sparse connectivity | Hardware-native mapping |
| Few parameters | Classical optimizer efficient |

**Sütun 2 — Zorluklar (kırmızı tonlar):**
| Zorluk | Etkisi |
|---|---|
| Barren plateau | Büyük $n, p$'de trainability |
| Measurement shots | Donanım süresi pahalı |
| Classical bottleneck | Queue latency |
| Gate errors | $p$ sınırı pratik |

**Alt bilgi:** Preskill 2018 + Blekos 2024 atıfları.

**Yorum cümlesi:** "QAOA NISQ-native algorithm — advantages and challenges coexist."

---

# Q&A İçgörüleri — Faz 2.6

## İçgörü 1: Scope İçi Gerçeklik Kontrolü

Scope'umuzun küçük ucunda (N=6, p=2) gerçek donanım başarı olasılığı ~%70. Yani sadece teorik bir egzersiz yapmıyoruz — gerçek donanımda da erişilebilir bir rejimdeyiz. N=10, p=3'e çıktığımızda bu olasılık %40'lara düşüyor (noise-free başarı).

**Süreç notu:** Bundan sonraki teorik fazlarda mekanik hesap sorusu değil, kavramsal/trend-yönü soruları tercih edilecek.

## İçgörü 2: Preskill Pozisyonlaması — Olgun Bir Bakış

**"NISQ cihazları keşif araçlarıdır, devrim değil"** — Bu ifade üç amaca hizmet ediyor:

1. **Hype'a karşı koruma** — quantum = büyüsel değil
2. **Gerçekçi hedefler** — araştırmacılara yön
3. **Anlamlı işi tanımlama** — variational, hybrid, problem-specific

QAOA tam bu pozisyonlamanın kalbinde. "NISQ-native" tasarım. Sunumda QAOA'yı **"aktif araştırma alanı"** olarak sunacağız, abartılı iddialarla değil.

## İçgörü 3: FTQC Geldiğinde QAOA'nın Değeri Artar

**İki katmanlı değer:**

**Katman 1 — Doğrudan kullanım:**
- FTQC'de QAOA büyük $p$ ile çalıştırılabilir
- Adiabatic limit → optimal çözüm garantisi

**Katman 2 — Tarihsel miras:**
- FTQC geldiğinde Shor, Grover, HHL, QPE gibi kanıtlanmış üstünlüğü olan algoritmalar baskın olabilir
- Ama QAOA'nın NISQ dönemindeki öncü rolü kalıcı:
  - Variational paradigma
  - Hybrid computing prensipleri
  - Problem-specific algoritma tasarımı
- Bu dersler FTQC dönemine taşınıyor

**Sunum çerçevesi:** QAOA "bugünün algoritması ama yarının mirası". Dürüst + değerli çerçeveleme.

---

# Özet — Faz 2.6'dan Çıkan Eldeki Taşlar

1. ✅ NISQ'in üç temel sınırlaması (coherence, gate error, shots)
2. ✅ QAOA'nın dört NISQ avantajı (shallow depth, sparse connectivity, noise tolerance, few params)
3. ✅ QAOA'nın beş NISQ zorluğu (barren plateau, shots, classical bottleneck, noise, connectivity)
4. ✅ Fault-tolerant vs NISQ karşılaştırması ve QAOA'nın her iki rejimdeki yeri
5. ✅ Quantum advantage tartışması — dürüst denge
6. ✅ Sunum için NISQ karnesi formatı (Slayt 10 taslağı)
7. ✅ Preskill pozisyonlamasının olgun yorumu
8. ✅ FTQC dönemine hazırlık — QAOA'nın sürdürülebilir algoritma özelliği

---

# Sırada: Faz 2.7 — Hocanın Notasyonuyla Son Hizalama

Faz 2'nin son alt-fazı. Bu alt-fazda:
- Hocanın 6 haftalık notasyonunu tekrar gözden geçir
- Faz 2.1-2.6'da kullandığımız gösterimleri karşılaştır
- Uyumsuzlukları tespit et ve düzelt
- Sunum için tutarlı notasyon seti belirle

Bu faz bitince Faz 2 %100 tamamlanmış olacak ve implementasyon aşamasına geçilebilir.
