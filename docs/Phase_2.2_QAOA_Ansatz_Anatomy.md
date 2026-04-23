# Faz 2.2 — QAOA Ansatz Anatomisi

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı
**Konvansiyon:** Yol 1 (negatif $H_C$, minimizasyon — Qiskit uyumlu)

---

## İçerik Haritası

- **Bölüm A:** Initial state $|\psi_0\rangle = H^{\otimes n}|0\rangle^{\otimes n}$
- **Bölüm B:** Cost operator $U_C(\gamma) = e^{-i\gamma H_C}$
- **Bölüm C:** Mixer operator $U_B(\beta) = e^{-i\beta H_B}$
- **Bölüm D:** p-layer yapısı ve adiabatic bağlantı önizlemesi

Faz 2.1'den elimizde: $H_C = \frac{1}{2}\sum_{(i,j)\in E}(Z_i Z_j - \mathbb{1})$, diyagonal yapısı, ground state = optimal cut. Kritik boşluk: $U_C$ tek başına olasılık dağılımını değiştiremez → mixer gerekli.

---

# BÖLÜM A — Initial State: Uniform Superposition

## A.1. Formül

$$|\psi_0\rangle = H^{\otimes n}|0\rangle^{\otimes n} = \frac{1}{\sqrt{2^n}} \sum_{z \in \{0,1\}^n} |z\rangle$$

Tüm $2^n$ computational basis state'i eşit genlikle içeren uniform superposition.

## A.2. Neden Uniform Superposition?

**Sebep 1: Unbiased prior.**
MaxCut'ın çözümünü bilmiyoruz. Hiçbir bitstring'i önden tercih etmemek için en nötr başlangıç uniform superposition'dır.

**Sebep 2: Mixer Hamiltonian'ın eigenstate'i.**
QAOA'nın mixer operatörü $H_B = \sum_i X_i$. Her qubit için $X|+\rangle = +|+\rangle$, dolayısıyla:

$$H_B |\psi_0\rangle = n |\psi_0\rangle$$

$|\psi_0\rangle$ $H_B$'nin bir eigenstate'i. Bu, QAOA'nın **adiabatic quantum computing** ile bağlantısının temel noktası (Bölüm D'de detaylandırılacak).

**Sebep 3: Hazırlık çok ucuz.**
Hocanın QDW2'de gördüğümüz üzere $H|0\rangle = |+\rangle$. $n$ qubit için paralel Hadamard: devre derinliği 1, gate sayısı $n$. NISQ cihazlarda pahalı olan 2-qubit gate'ler değil, tek-qubit gate'ler bedava sayılır.

## A.3. Geometrik Sezgi

$n$ qubit'lik Hilbert uzayı $2^n$ boyutlu. Uniform superposition bu uzayın "merkezinde". QAOA'nın görevi bu merkezden başlayıp olasılık kütlesini $H_C$'nin ground state'inin bulunduğu köşelere kaydırmak.

---

# BÖLÜM B — Cost Operator: $U_C(\gamma) = e^{-i\gamma H_C}$

## B.1. Operatörün Tanımı

$$U_C(\gamma) = e^{-i\gamma H_C} = \exp\left(-i\gamma \cdot \frac{1}{2}\sum_{(i,j) \in E}(Z_i Z_j - \mathbb{1})\right)$$

$\gamma \in \mathbb{R}$ bir variational parametre. "$H_C$ Hamiltonian'ı altında $\gamma$ süre zaman evrimi" — Schrödinger denkleminden, $\hbar = 1$.

## B.2. Toplamı Çarpıma Çevirme

$Z_i Z_j$ terimleri birbirleriyle **commute** eder (hepsi $Z$ ve $\mathbb{1}$'den oluşuyor, farklı qubit çiftlerine etki ediyorlar). Bu yüzden:

$$e^{-i\gamma H_C} = \prod_{(i,j) \in E} e^{-i\gamma \cdot \frac{1}{2}(Z_i Z_j - \mathbb{1})}$$

Global $\mathbb{1}$ faz terimi gözlemlenemeyen bir global phase olduğu için ihmal edilir:

$$\boxed{\; U_C(\gamma) = \prod_{(i,j) \in E} e^{-i\frac{\gamma}{2} Z_i Z_j} \;}$$

Cost operator, her kenar için bir $e^{-i\frac{\gamma}{2} Z_i Z_j}$ gate'inin çarpımına dönüşüyor.

## B.3. Tek Kenar Terimi: $R_{ZZ}$ Gate

Hocanın QDW3'teki $R_z$ türetmesi:

$$R_z(\theta) = e^{-i\frac{\theta}{2}\sigma_z} = \begin{pmatrix}e^{-i\theta/2} & 0 \\ 0 & e^{i\theta/2}\end{pmatrix}$$

Bizim ihtiyacımız **iki qubit** $Z_i Z_j$ rotasyonu: $R_{ZZ}(\theta) = e^{-i\frac{\theta}{2} Z_i Z_j}$.

$Z_i Z_j$ iki qubit'in paritesine bağlı etki eder:

$$Z_i Z_j |z_i z_j\rangle = (-1)^{z_i \oplus z_j} |z_i z_j\rangle$$

- $|00\rangle, |11\rangle$ (parite 0): $+1$
- $|01\rangle, |10\rangle$ (parite 1): $-1$

## B.4. $R_{ZZ}$ Devre Ayrışımı

$$R_{ZZ}(\theta) = \text{CNOT}_{i,j} \cdot (\mathbb{1}_i \otimes R_z(\theta)_j) \cdot \text{CNOT}_{i,j}$$

Devre şeması:

```
qubit i: ──●─────────────●──
           │             │
qubit j: ──⊕── R_z(θ) ──⊕──
```

**Neden işliyor?**
1. İlk CNOT: $|z_i z_j\rangle \to |z_i, z_i \oplus z_j\rangle$ — qubit $j$ artık pariteyi taşıyor
2. $R_z(\theta)$: pariteye bağlı faz uyguluyor, $e^{-i\frac{\theta}{2}(-1)^{z_i \oplus z_j}}$
3. İkinci CNOT: durumu eski haline geri çeviriyor

Sonuç: $e^{-i\frac{\theta}{2} Z_i Z_j}$.

Bu, hocanın QDW3'teki "exponent of Hamiltonian as a gate" sezgisinin doğrudan iki-qubit genellemesi. Pedagojik köprü: QAOA cost operator, dinleyicilerin zaten bildiği $R_z$ sezgisinin doğal uzantısı.

## B.5. Cost Operator'ün Kaynak Maliyeti

Her kenar için:
- **2 CNOT gate** (2-qubit)
- **1 $R_z(\gamma)$ gate** (tek-qubit)

Toplam devre, $|E|$ kenar için:
- **$2|E|$ CNOT gate**
- **$|E|$ tek-qubit rotasyon gate**

**Graf yapısına göre scaling:**
- K_N (tam graf): $|E| = N(N-1)/2$ → CNOT sayısı $\sim N^2$
- N-düğümlü 3-regular graf: $|E| = 3N/2$ → CNOT sayısı $\sim 3N$ (lineer)
- K₃ üçgen (özel durum, 2-regular): $|E| = 3$ → 6 CNOT

Bu **Complexity slaytlarındaki** "gate count vs N" grafiklerinin scaling'inin matematiksel gerekçesi.

## B.6. Cost Operator'ün Fiziksel Anlamı

Yol 1 konvansiyonunda $H_C |z\rangle = -C(z)|z\rangle$, dolayısıyla:

$$U_C(\gamma) |z\rangle = e^{+i\gamma C(z)} |z\rangle$$

**Cost operator basis state'ler arasında karışma yaratmaz, sadece onları faz bilgisi ile etiketler.** "Hangi bitstring'in iyi çözüm olduğu" bilgisi kuantum sistemin içine yazılır, ama henüz olasılık dağılımına dönüşmemiştir. Bunun için mixer lazım.

---

# BÖLÜM C — Mixer Operator: $U_B(\beta) = e^{-i\beta H_B}$

## C.1. Neden $X$ Tabanlı?

Faz 2.1 B.4'ün cevabı burada. Cost operator diyagonal olduğu için basis state'ler arasında karışma yaratamıyor. Bu boşluğu kapatmak için $Z$ basis'inde diyagonal OLMAYAN bir operatöre ihtiyaç var.

Pauli $X$ bu özelliği taşır:

$$X|0\rangle = |1\rangle, \qquad X|1\rangle = |0\rangle$$

$X$ computational basis state'leri birbirine dönüştürür — gerçek karışma yaratır.

## C.2. Mixer Hamiltonian

$$H_B = \sum_{i=0}^{n-1} X_i$$

İki önemli özellik:

**1. Uniform superposition $H_B$'nin eigenstate'i:**

Her $X_i$ için $X|+\rangle = +|+\rangle$. Qubit-wise $|\psi_0\rangle = |+\rangle^{\otimes n}$ olduğundan:

$$H_B |\psi_0\rangle = n |\psi_0\rangle$$

Bu özellik QAOA'nın **adiabatic quantum computing** temelinin merkezinde.

**2. Tek-qubit terimlerden oluşur:**

Tüm $X_i$'ler commute eder (farklı qubit'lerde). Bu, exponential ayrıştırmasını kolaylaştırır.

## C.3. Mixer Operator'ün Devresi

$X_i$'ler commute ettiği için:

$$U_B(\beta) = e^{-i\beta \sum_i X_i} = \prod_{i=0}^{n-1} e^{-i\beta X_i}$$

Tek qubit:

$$e^{-i\beta X_i} = \cos(\beta)\mathbb{1} - i\sin(\beta) X_i$$

Hocanın QDW3'teki $R_x$ türetmesi:

$$R_x(\theta) = e^{-i\frac{\theta}{2}\sigma_x} = \cos(\theta/2)\mathbb{1} - i\sin(\theta/2)\sigma_x$$

Karşılaştırma: $e^{-i\beta X_i} = R_x(2\beta)_i$. Yani:

$$\boxed{\; U_B(\beta) = \prod_{i=0}^{n-1} R_x(2\beta)_i \;}$$

**$n$ qubit'e paralel uygulanan $R_x(2\beta)$ gate'leri.** Devre derinliği: 1 (hepsi paralel). Gate sayısı: $n$ (hepsi tek-qubit).

## C.4. Mixer'ın Kaynak Maliyeti

Her $U_B(\beta)$ katmanı için:
- **$n$ tek-qubit rotasyon gate**
- **0 CNOT** — mixer 2-qubit gate kullanmaz

Bu çok önemli: QAOA'nın toplam 2-qubit gate bütçesi neredeyse tamamen cost operator'den gelir.

## C.5. Mixer Operator'ün Fiziksel Anlamı

$R_x(2\beta)$ her qubit'i Bloch küresinde $x$-ekseni etrafında $2\beta$ açısıyla döndürür. Bu computational basis state'ler arasında olasılık genliği transferi demek.

**Cost + Mixer birlikte nasıl çalışır:**
1. $U_C(\gamma)$ her basis state'e "bu çözüm ne kadar iyi" bilgisini faz olarak yazar
2. $U_B(\beta)$ basis state'leri karıştırır
3. Karıştırma sırasında fazlar **quantum interference** yaratır
4. İyi çözümlerin genlikleri **constructive**, kötülerin **destructive** girişim ile değişir

Bu, Grover's algorithm'daki "amplitude amplification" mantığının variational/adaptive versiyonu. Grover sabit iterasyon yaparken, QAOA parametrelerini problem instance'ına göre optimize eder.

## C.6. Sıralama Neden $U_B U_C |\psi_0\rangle$?

**Kritik nokta — Kavrayış 2'nin cevabı:**

Uniform superposition $|\psi_0\rangle$ mixer'ın eigenstate'idir. Eigenstate'e $U_B$ uygulamak sadece global phase katar:

$$U_B(\beta) |\psi_0\rangle = e^{-i\beta n} |\psi_0\rangle$$

Global phase ölçümde görülmez. Yani $U_C U_B |\psi_0\rangle$ sıralamasında $U_B$ hiç iş yapmaz, algoritma $U_C |\psi_0\rangle$'a çöker — ve $U_C$ sadece faz yazdığı için ölçüm tamamen rastgele.

**QAOA'da sıralama $U_B U_C |\psi_0\rangle$ olmak ZORUNDA.** Cost önce uygulanmalı ki fazlar yazılsın, sonra mixer bu fazları genlik değişikliğine çevirebilsin. Bu sıralama tesadüf değil, algoritmanın temeli.

---

# BÖLÜM D — p-Layer Yapısı ve Adiabatic Bağlantı

## D.1. QAOA Ansatz'ının Tam Formu

$p$ bir pozitif tamsayı (katman sayısı). QAOA ansatz:

$$|\psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle = U_B(\beta_p) U_C(\gamma_p) \cdots U_B(\beta_1) U_C(\gamma_1) |\psi_0\rangle$$

- $\boldsymbol{\gamma} = (\gamma_1, \ldots, \gamma_p)$ ve $\boldsymbol{\beta} = (\beta_1, \ldots, \beta_p)$ — toplam $2p$ variational parametre
- Katman sırası: **önce cost, sonra mixer**
- Her katmanın kendi parametreleri var

## D.2. Optimizasyon Objektifi

QAOA'nın minimize ettiği (Yol 1):

$$F_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) = \langle \psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) | H_C | \psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) \rangle$$

Klasik optimizer (COBYLA, SPSA, L-BFGS-B) bu objektifi minimize edecek $\boldsymbol{\gamma}^*, \boldsymbol{\beta}^*$ arar.

## D.3. Adiabatic Bağlantı

QAOA, **adiabatic quantum computing (AQC)**'nin gate-model karşılığıdır. AQC'de fikir:

Kolay bir Hamiltonian $H_B$ (ground state'i biliniyor: uniform superposition) ile başla, yavaşça hedef $H_C$'ye geç:

$$H(t) = (1 - t/T) H_B + (t/T) H_C, \quad t \in [0, T]$$

**Adiabatic teoremi:** $T$ yeterince büyükse, sistem başlangıç ground state'inden final ground state'ine geçer (yani $H_C$'nin ground state'i = optimal MaxCut çözümü).

**Trotter-Suzuki ayrıklaştırması:**

$$e^{-iH(t)\Delta t} \approx e^{-i(1-s)H_B \Delta t} \cdot e^{-isH_C \Delta t}$$

$p$ ayrık adım → QAOA ansatz'ı.

**Kritik farklar:**
- AQC: evrim zamanı ve ara adımlar sabit
- QAOA: $\gamma_k, \beta_k$ parametreleri **optimize edilir** → kısa devrelerle iyi sonuçlar alınabilir

## D.4. $p$ Büyüdükçe Ne Olur?

- **$p \to \infty$:** QAOA optimal çözümü bulabilir (adiabatic teoremi)
- **$p = 1$:** Farhi'nin 3-regular graflar için $r \geq 0.6924$ alt sınırı
- **$p$ artarsa:** approximation ratio iyileşir, devre derinliği/gate sayısı artar
- **NISQ trade-off:** küçük $p$ donanım-uyumlu, büyük $p$ daha iyi çözüm

Scaling deneylerimizde ($p \in \{1, 2, 3\}$) bu trade-off görselleştirilecek.

## D.5. QAOA Variational Loop

```
1. İlk parametre tahmini: γ_0, β_0
2. Kuantum devresi hazırla: |ψ_p(γ, β)⟩
3. Ölçüm yap, beklenen değeri hesapla: F_p(γ, β)
4. Klasik optimizer parametreleri güncelle
5. 2-4'ü yakınsayana kadar tekrarla
6. Optimal γ*, β* ile ölçüm yap, bitstring al
```

Bu **hybrid quantum-classical** yapı NISQ-uyumluluğun kaynağı.

---

# Tam QAOA Devre Şeması (Kavramsal)

```
|0⟩ ─ H ─┤                           ├─┤ R_x(2β) ├─ ... (p kez)
|0⟩ ─ H ─┤                           ├─┤ R_x(2β) ├─ ...
|0⟩ ─ H ─┤   cost operator U_C(γ)    ├─┤ R_x(2β) ├─ ...
|0⟩ ─ H ─┤  (kenar başına R_ZZ(γ))   ├─┤ R_x(2β) ├─ ...
         └────────────────────────────┘
         \____________________ p kez tekrar ____________________/
                                                               │
                                                           Ölçüm
```

---

# Faz 2.2 Kritik İçgörüleri

## İçgörü 1: Graf Terminolojisi

- **K_N (tam graf):** N düğüm arası tüm kenarlar, $|E| = N(N-1)/2$
- **N-regular graf:** Her düğümün derecesi N (düğüm sayısıyla karıştırılmamalı)
- **K₃ (üçgen):** 3 düğüm, 3 kenar, **2-regular** (3-regular değil)
- Sunum tablomuzda: N=3 için K₃ (özel durum), N≥4 için random 3-regular

## İçgörü 2: Uniform Superposition Mixer'ın Eigenstate'i

$U_B |\psi_0\rangle = e^{-i\beta n} |\psi_0\rangle$ (sadece global phase). Bu yüzden QAOA sıralaması $U_B U_C$ olmak zorunda, $U_C U_B$ değil.

## İçgörü 3: Konvansiyon İşaret Çevirisi

Yol 1 ↔ Yol 2 arasında geçiş:
- **Optimal $\gamma^*$:** işaret değiştirir ($\gamma^*_{\text{Yol 1}} = -\gamma^*_{\text{Yol 2}}$)
- **Optimal $\beta^*$:** aynı kalır (mixer değişmiyor)
- **Approximation ratio:** aynı (konvansiyondan bağımsız fiziksel büyüklük)

Scaling deneylerinde Farhi 2014 (Yol 2) değerleriyle karşılaştırma yaparken $\gamma$ işaret çevirisi hesaba katılacak.

## İçgörü 4: CNOT Sayısı Cost Operator'den Gelir

- Cost operator (per kenar): 2 CNOT
- Mixer (per qubit): 0 CNOT
- Toplam CNOT ($p$ katman için): $2p|E|$
- K₃, p=1: $2 \cdot 1 \cdot 3 = 6$ CNOT
- N-qubit 3-regular graf, p=1: $2 \cdot 1 \cdot (3N/2) = 3N$ CNOT

---

# Sırada: Faz 2.3 — Adiabatic Theorem Bağlantısı

Faz 2.2.D'de önizlemesini verdiğimiz adiabatic bağlantının tam matematiksel detayı:

- Adiabatic teoremi ve şartları (gap'in rolü)
- Continuous Hamiltonian evrimden Trotter ayrıklaştırmasına
- QAOA ansatz'ının bu ayrıklaştırmadan doğal olarak çıkışı
- Parametre optimizasyonu: adiabatic vs variational yaklaşım
- Farhi 2014 $p \to \infty$ teoreminin kavramsal gerekçesi
