# Faz 2.5 — Variational Döngü ve Klasik Optimizasyon

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı

---

## İçerik Haritası

- **Bölüm A:** Hybrid quantum-classical yapı
- **Bölüm B:** Klasik optimizer seçimleri
- **Bölüm C:** Parametre uzayı yapısı (boyut, periyodiklik, landscape)
- **Bölüm D:** Initialization stratejileri
- **Bölüm E:** Barren plateau kavramı (önizleme)
- **Bölüm F:** Convergence kriterleri
- **Bölüm G:** Tam QAOA pseudocode
- **Q&A İçgörüleri:** Üç kritik kavram (grid explosion dahil)

Faz 2.4'ten: ölçüm ve approximation ratio. Bu fazda variational döngüyü ve optimizer seçimlerini oturtuyoruz.

---

# BÖLÜM A — Hybrid Quantum-Classical Yapı

## A.1. Neden Hybrid?

QAOA'nın dahiyane fikri **iş bölümü**:

- **Kuantum kısım:** Parametreli durum hazırlama + ölçüm → $\langle H_C \rangle$ tahmini
- **Klasik kısım:** Parametreleri güncelle → yeni $\gamma, \beta$ öner

Bu döngü yakınsayana kadar tekrarlanır.

## A.2. Variational Döngü Şeması

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│   Klasik başlangıç: γ₀, β₀                          │
│              │                                      │
│              ▼                                      │
│   ┌─────────────────────┐                           │
│   │  KUANTUM KISIM      │                           │
│   │                     │                           │
│   │  1. Devre hazırla   │  ◄──── γₖ, βₖ             │
│   │  2. Ölçüm yap       │                           │
│   │  3. ⟨H_C⟩ hesapla   │  ────► F(γₖ, βₖ)          │
│   │                     │                           │
│   └─────────────────────┘                           │
│              │                                      │
│              ▼                                      │
│   ┌─────────────────────┐                           │
│   │  KLASİK KISIM       │                           │
│   │                     │                           │
│   │  4. F değerini al   │                           │
│   │  5. Parametre       │  ────► γₖ₊₁, βₖ₊₁         │
│   │     güncelle        │                           │
│   │                     │                           │
│   └─────────────────────┘                           │
│              │                                      │
│              ▼                                      │
│   Yakınsama kontrolü:                               │
│   ΔF < ε veya iter > max_iter                       │
│              │                                      │
│              ▼                                      │
│   Optimal γ*, β* ile ölçüm al → bitstring           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## A.3. İş Bölümünün Mantığı

**Kuantum'un avantajı:** $|\psi_p(\gamma, \beta)\rangle$ üzerindeki $\langle H_C \rangle$'yi klasik hesaplamak exponentially zor (genelde $O(2^n)$). Kuantum devre bunu paralel yapar.

**Klasik'in avantajı:** Optimizasyon algoritmaları (gradient descent, BFGS, Nelder-Mead) on yıllardır olgun. Parametre uzayında yön bulma işini klasik yapmak akıllıca.

Her şey kuantum olsaydı: quantum gradient estimation (parameter-shift rule) gerekirdi, her gradient bileşeni için $O(1)$ ek devre. Gradient-free optimizer (COBYLA) bu yükten kurtarır.

---

# BÖLÜM B — Klasik Optimizer Seçimleri

## B.1. Üç Ana Aile

### Aile 1: Gradient-Free
- **COBYLA** (Constrained Optimization BY Linear Approximation)
- **Nelder-Mead** (simplex method)
- **SPSA** (Simultaneous Perturbation Stochastic Approximation)

Avantaj: Gradient gerek yok.
Dezavantaj: Yüksek boyutta yavaş.

### Aile 2: Gradient-Based
- **L-BFGS-B**
- **ADAM**

Avantaj: Hızlı yakınsama.
Dezavantaj: Her iterasyon için gradient → ek devreler.

### Aile 3: Stochastic
- **SPSA** (hem gradient-free hem stochastic)

Avantaj: Noisy function'larda dayanıklı.
Dezavantaj: Gürültülü yakınsama.

## B.2. Bizim Seçimimiz: COBYLA

Gerekçeler:
1. **Gradient-free:** Ek devre yok
2. **Küçük parametre sayısı:** $2p$ (p=3 için 6) → COBYLA ideal
3. **Scipy standardı:** Kod basit
4. **Literatür:** Farhi 2014 ve follow-up'lar COBYLA kullanıyor

Alternatif (ileride noise eklersek, scope dışı): SPSA.

---

# BÖLÜM C — Parametre Uzayı Yapısı

## C.1. Parametre Boyutu

| $p$ | Parametre sayısı |
|---|---|
| 1 | 2 |
| 2 | 4 |
| 3 | 6 |

QAOA'nın parametre uzayı küçük — NISQ avantajı. VQE genelde $O(n \cdot L)$ parametre kullanır.

## C.2. Parametre Periyodikliği

**$\gamma$ periyodikliği (integer-valued MaxCut cost):**

$$U_C(\gamma) = U_C(\gamma + 2\pi) \quad \Rightarrow \quad \gamma \in [0, 2\pi)$$

**$\beta$ periyodikliği:**

$$U_B(\beta) = U_B(\beta + \pi) \quad \Rightarrow \quad \beta \in [0, \pi)$$

**Ek simetri:** $\gamma \to -\gamma, \beta \to -\beta$ → complex conjugate, aynı expectation.

MaxCut'ta genelde $\gamma \in [0, \pi)$ ve $\beta \in [0, \pi/2)$ yeterli.

## C.3. Landscape Karakteri

- **Smooth:** nispeten pürüzsüz
- **Periyodik:** yukarıdaki yapı
- **Çoklu lokal minima:** global garanti yok

Parametre uzayı landscape görseli Faz 4'te üretilecek (p=1 için 2D $\gamma$-$\beta$ heatmap).

---

# BÖLÜM D — Initialization Stratejileri

## D.1. Strateji 1: Random Initialization

$\gamma_k, \beta_k$ uniform random. Basit, ama lokal minimum riski yüksek.

## D.2. Strateji 2: Adiabatic-Inspired

$$\gamma_k = \frac{k}{p+1} \cdot \Delta t, \qquad \beta_k = \left(1 - \frac{k}{p+1}\right) \cdot \Delta t$$

İyi basin of attraction'da başlar → hızlı yakınsama.

## D.3. Strateji 3: Parameter Concentration

**Gözlem** (Brandao-Broughton-Farhi-Gutmann-Neven 2018, Blekos 2024): Benzer graflar benzer optimal parametreler verir.

**Pratik:** Küçük graf için optimal bul → benzer büyük graflar için başlangıç. Transfer learning benzeri.

## D.4. Strateji 4: Grid Search + Refinement

**p=1 için (2 boyut):**
1. Kaba grid'de $F(\gamma, \beta)$ hesapla ($50 \times 50 = 2500$)
2. En iyi noktayı başlangıç al
3. COBYLA ile refine

**p≥2 için grid patlıyor** (Q&A İçgörü 2'de detay) — **layer-by-layer** yaklaşım kullanılır:
- p=1 optimal bul
- p=2 için: p=1 sonuçlarını başlangıç + yeni katman parametrelerini küçük grid'le ara + COBYLA
- p=3 için: p=2 sonuçlarını başlangıç + benzer adım

## D.5. Bizim Stratejimiz

| p | Yaklaşım |
|---|---|
| 1 | Grid (50×50) + COBYLA refine |
| 2 | Layer-by-layer: p=1 sonucundan başla + küçük 2D grid + COBYLA |
| 3 | Layer-by-layer: p=2 sonucundan başla + küçük 2D grid + COBYLA |

Plus: her kombinasyon için multistart (birkaç farklı başlangıç) ile doğrulama.

Implementasyon aşamasında detaylandırılacak.

---

# BÖLÜM E — Barren Plateau (Önizleme)

## E.1. Problem Tanımı

**Barren plateau** (McClean et al. 2018): Gradient'lerin üstel küçülmesi.

$$\text{Var}[\partial_\theta F] \sim \frac{1}{2^n}$$

Optimizer "düz plato"da kaybolur.

## E.2. QAOA'da Durum

**Dayanıklı kılan faktörler:**
- Shallow depth (küçük $p$)
- Problem-spesifik Hamiltonian
- Lokal etkileşimler

**Riski büyüten faktörler:**
- $p$ arttıkça risk artar
- Büyük $n$ + random init tehlikeli
- Noise-induced barren plateau (Wang et al. 2021)

**Bizim scope'ta** (N≤10, p≤3, noise yok): pratik problem değil.

## E.3. Sunum Bağlantısı

NISQ karnesi slaytında kavramsal düzeyde tartışılacak.

---

# BÖLÜM F — Convergence Kriterleri

## F.1. Durma Koşulları

**Kriter 1:** $|F_k - F_{k-1}| < \epsilon_F$
**Kriter 2:** $\|\boldsymbol{\theta}_k - \boldsymbol{\theta}_{k-1}\| < \epsilon_\theta$
**Kriter 3:** $k > k_{\max}$

## F.2. Bizim Değerlerimiz

- $\epsilon_F = 10^{-6}$
- $\epsilon_\theta = 10^{-6}$
- $k_{\max} = 200$

COBYLA default'ları benzer.

## F.3. Yakınsama Eğrisi

Sunumda **optimizasyon eğrisi** görseli Faz 4'te üretilecek:
- Y-axis: $\langle H_C \rangle$ veya approximation ratio
- X-axis: iterasyon numarası

"Explicit Demo (20 puan)" kriterine hizmet eder.

---

# BÖLÜM G — Tam QAOA Pseudocode

```
Input: Graf G = (V, E), p, ε, max_iter
Output: Bitstring z*

1. H_C ← build_cost_hamiltonian(G)    # Yol 1
2. H_B ← sum(X_i for i in V)

3. # Initialization
   if p == 1:
       grid_points ← 50×50 grid in [0,π) × [0,π/2)
       best_params ← argmin(evaluate(γ,β) for (γ,β) in grid_points)
   else:
       prev_params ← load_optimal(p-1)
       new_params_grid ← small grid for new layer
       best_params ← [prev_params, argmin(eval with new layer)]

4. # Local refinement
   γ*, β* ← scipy.minimize(
       objective = lambda params: expectation(H_C, |ψ_p(params)⟩),
       x0 = best_params,
       method = 'COBYLA',
       tol = ε,
       options = {'maxiter': max_iter}
   )

5. # Final measurement (statevector mode → exact)
   |ψ_final⟩ ← QAOA_circuit(γ*, β*)
   samples ← measure(|ψ_final⟩, N_shots)

6. # Post-selection
   z* ← argmax(C(z) for z in samples)

7. return z*, C(z*), γ*, β*
```

Bu pseudocode implementasyon iskeletinin çekirdeği.

---

# Q&A İçgörüleri — Faz 2.5

## İçgörü 1: Hybrid Yapının Ana Avantajı

**Soru:** Neden her şey kuantum veya her şey klasik değil de hybrid?

**Cevap — İki temel neden:**

1. **Parametre optimizasyonu:** Klasikte kolay (olgun ekosistem: scipy, nlopt, cma-es). Kuantumda gradient için parameter-shift rule → her gradient bileşeni için ek devre. Gradient-free optimizer (COBYLA) kuantum yükünü elimine eder.

2. **Cost/mixer operatörlerin uygulanması:** Klasikte $\langle H_C \rangle$ hesabı $O(2^n)$ — hepsi enumerate etmen gerek. Kuantum paralelizmi bu işi "native" yapar.

**Ek nokta:** Hybrid yaklaşım her iki dünyanın en iyi özelliklerini birleştiriyor — klasik olgun optimizasyon algoritmaları + kuantum paralellik.

## İçgörü 2: Grid Search Curse of Dimensionality (Kritik Kavram)

**Soru:** p=3 için 20 grid noktası/boyut → kaç değerlendirme?

**Cevap:** Grid search **Cartesian product** üretir. Her boyutta bağımsız seçim:

$$\text{değerlendirme sayısı} = 20^{\text{boyut}}$$

| $p$ | Boyut | Grid boyutu | Pratik |
|---|---|---|---|
| 1 | 2 | $20^2 = 400$ | rahat |
| 2 | 4 | $20^4 = 160\text{k}$ | sınırda |
| 3 | 6 | $20^6 = 64\text{M}$ | **imkânsız** |

**Curse of dimensionality** — grid search boyutla exponential patlar.

**Bu neden Faz 2.5.D'de layer-by-layer stratejisi önerdik:**
- Naive grid p≥2'de ölçeklenmiyor
- Layer-by-layer: her katmanı ayrı ayrı ara, önceki katmanların optimal değerlerini kullan
- Her adımda sadece 2 yeni parametre için arama → $20^2 = 400$ değerlendirme

**Sunum bağlantısı:** Bu içgörü Complexity slaytında QAOA'nın scaling analizinde yer alacak — **algoritma ölçeklenir mi sadece devre karmaşıklığı değil, optimizer stratejisinin ölçeklenmesine de bağlı**.

## İçgörü 3: Barren Plateau Yönetilebilir Risk

**Soru:** Barren plateau QAOA'yı çıkmaza sokar mı?

**Cevap:** Yönetilebilir risk, game-over değil.

**QAOA'yı koruyan faktörler:**
- Shallow depth (küçük $p$)
- Problem-spesifik Hamiltonian yapısı (lokal, sparse)
- Smart initialization (adiabatic-inspired, transfer learning)

**Literatür durumu:**
- Tamamen çözülmüş değil
- NISQ döneminde aktif araştırma alanı
- Yeni ansatz'lar (ADAPT-QAOA, multi-angle QAOA) barren plateau'yu azaltmaya çalışıyor

**Bizim scope'ta** pratik problem değil, NISQ karnesinde kavramsal olarak tartışılacak.

---

# Özet — Faz 2.5'ten Çıkan Eldeki Taşlar

1. ✅ Hybrid quantum-classical yapı ve variational döngü şeması
2. ✅ Klasik optimizer aileleri ve COBYLA seçimi
3. ✅ Parametre uzayının yapısı: boyut, periyodiklik, simetri
4. ✅ Initialization stratejileri (4 yaklaşım)
5. ✅ Grid search curse of dimensionality — p=3'te $20^6$ değerlendirme
6. ✅ Layer-by-layer initialization: naive grid'in ölçek problemini çözer
7. ✅ Barren plateau: yönetilebilir risk, QAOA korumalı ama yönetilmeli
8. ✅ Convergence kriterleri ve değerler
9. ✅ Tam QAOA pseudocode (implementasyon iskeleti)

---

# Sırada: Faz 2.6 — NISQ Karnesi ve Kritik Performans Sınırları

- QAOA-spesifik NISQ avantajları (derinlik, variational yapı, gürültü toleransı)
- QAOA-spesifik NISQ zorlukları (barren plateau, ölçüm bütçesi, klasik optimizer darboğazı, noise accumulation)
- "Quantum advantage" iddiası: nerede, ne zaman, nasıl?
- Sunum için QAOA NISQ karnesi tablo formatı
