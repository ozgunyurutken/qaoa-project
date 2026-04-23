# Faz 2.1 — MaxCut'tan Ising Hamiltonian'a

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı
**Ana Referans Konvansiyonu:** Yol 1 (negatif $H_C$, minimizasyon — Qiskit/implementasyon uyumlu)

---

## İçerik Haritası

- **Bölüm A:** Klasik MaxCut problemi + binary→spin dönüşümü
- **Bölüm B:** Ising Hamiltonian + eigenspectrum sezgisi
  - B1: Klasik $C(\mathbf{s})$'ten kuantum $H_C$'ye köprü
  - B2: Eigenstate yapısı ve konvansiyon seçimi
  - B3: K₃ örneğinin tam spektrumu

---

# BÖLÜM A — Klasik MaxCut Problemi + Binary→Spin Dönüşümü

## A.1. MaxCut Nedir?

Bir **ağırlıksız, yönsüz graf** $G = (V, E)$ verilsin. $V$ düğüm kümesi, $E$ ise kenar kümesi. Amaç: düğümleri iki kümeye bölmek — $S \subseteq V$ ve tümleyeni $V \setminus S$ — öyle ki **iki kümeyi kesen (crossing) kenar sayısı maksimum olsun**.

Cut size (kesim büyüklüğü):

$$C(S) = |\{(u,v) \in E : u \in S, \ v \notin S\}|$$

Optimum:

$$C^* = \max_{S \subseteq V} C(S)$$

**Neden önemli?** MaxCut **NP-hard** — klasik olarak verimli kesin çözümü bilinmeyen bir problem. Polinomiyal zamanda en iyi bilinen klasik yaklaşık algoritma Goemans-Williamson (1995), yaklaşıklık oranı $\approx 0.878$. Bu nedenle MaxCut, yeni (klasik veya kuantum) optimizasyon algoritmalarının denenmesi için **benchmark** olarak kullanılır.

## A.2. Bit Değişkenleri ile Formülasyon

Her düğüm $i \in V$ için bir ikili değişken:

$$x_i \in \{0, 1\}, \quad x_i = \begin{cases} 0 & \text{eğer } i \in S \\ 1 & \text{eğer } i \notin S \end{cases}$$

Bir $(i,j)$ kenarı iki kümeyi **kesiyorsa**, $x_i \neq x_j$. Gösterge fonksiyonu olarak:

$$\mathbb{1}[x_i \neq x_j] = x_i + x_j - 2 x_i x_j$$

O zaman cut objective:

$$C(\mathbf{x}) = \sum_{(i,j) \in E} (x_i + x_j - 2 x_i x_j)$$

MaxCut problemi:

$$\mathbf{x}^* = \arg\max_{\mathbf{x} \in \{0,1\}^n} C(\mathbf{x})$$

## A.3. Neden İkili Değişkenden Spin Değişkenine Geçiyoruz?

Kuantum devrelerin doğal dili **Pauli-Z operatörü**. Hocanın QDW2'de verdiği spektral ayrışım:

$$Z = |0\rangle\langle 0| - |1\rangle\langle 1|, \qquad Z|0\rangle = +1\,|0\rangle, \quad Z|1\rangle = -1\,|1\rangle$$

Yani $Z$'nin özdeğerleri $\pm 1$ — $\{+1, -1\}$ spin değişkenleriyle doğal olarak eşleşiyor.

**Dönüşüm:**

$$s_i = 1 - 2 x_i \quad \Leftrightarrow \quad x_i = \frac{1 - s_i}{2}$$

Eşleme tablosu:

| $x_i$ | $s_i$ | Anlamı |
|---|---|---|
| $0$ | $+1$ | $i \in S$ |
| $1$ | $-1$ | $i \notin S$ |

## A.4. Cost Function'ı Spin Değişkenleri Cinsinden Yazma

$x_i = (1 - s_i)/2$ ifadesini her bir kenar teriminde yerine koyarsak:

$$x_i + x_j - 2 x_i x_j = \frac{(1 - s_i) + (1 - s_j)}{2} - \frac{(1 - s_i)(1 - s_j)}{2}$$

$$= \frac{1}{2}\left[ 1 - s_i s_j \right]$$

**Sonuç:**

$$\boxed{\; x_i + x_j - 2 x_i x_j = \frac{1 - s_i s_j}{2} \;}$$

Doğrulama:
- Eğer $s_i = s_j$ (aynı kümede): $\frac{1 - 1}{2} = 0$ → kesim katkısı yok ✓
- Eğer $s_i \neq s_j$ (farklı kümelerde): $\frac{1 - (-1)}{2} = 1$ → kesim katkısı 1 ✓

## A.5. Klasik MaxCut Cost Function'ı — Spin Formu

$$C(\mathbf{s}) = \sum_{(i,j) \in E} \frac{1 - s_i s_j}{2}$$

Bu **tamamen klasik** bir optimizasyon problemi — henüz hiçbir kuantum yok. Amaç:

$$\mathbf{s}^* = \arg\max_{\mathbf{s} \in \{-1,+1\}^n} C(\mathbf{s})$$

## A.6. Üçgen Örneği (K₃) ile Doğrulama

3 düğüm, 3 kenar: $E = \{(0,1), (1,2), (0,2)\}$. 8 konfigürasyonun enumerasyonu:

| $s_0$ | $s_1$ | $s_2$ | $s_0 s_1$ | $s_1 s_2$ | $s_0 s_2$ | $C(\mathbf{s})$ |
|---|---|---|---|---|---|---|
| +1 | +1 | +1 | +1 | +1 | +1 | 0 |
| +1 | +1 | −1 | +1 | −1 | −1 | **2** |
| +1 | −1 | +1 | −1 | −1 | +1 | **2** |
| +1 | −1 | −1 | −1 | +1 | −1 | **2** |
| −1 | +1 | +1 | −1 | +1 | −1 | **2** |
| −1 | +1 | −1 | −1 | −1 | +1 | **2** |
| −1 | −1 | +1 | +1 | −1 | −1 | **2** |
| −1 | −1 | −1 | +1 | +1 | +1 | 0 |

**Sonuç:** $C^* = 2$, 6 tane optimal çözüm var. K₃ tek (odd-length) döngü içerdiği için **3 kenarın üçü birden kesilemez** — en iyisi 2. Bu "triangle frustration" fenomeni, MaxCut'ın klasik olarak da zor olmasının temel nedenlerinden biri.

## A.7. Kritik İçgörüler (Kavrayış Kontrol)

**MaxCut'ın zorluğu nereden geliyor?**

Problem **kuadratik + ayrık**. Sadece kuadratik olmak zorluk için yeterli değil (sürekli değişkenlerle polinomiyal zamanda çözülür). Ama değişkenler **ikili** ($\{0,1\}$ veya spin'de $\pm 1$) olunca problem **Quadratic Unconstrained Binary Optimization (QUBO)** sınıfına girer ve NP-hard olur.

**Neden?** $x_i x_j$ çarpım terimi "değişkenler arasında etkileşim" demek — bir değişkenin optimal değeri, diğer değişkenlerin aldığı değere bağlı. Lokal ardışık iyileştirmeler yanlış çözümlerde sıkışabilir.

**Frustration:** Bazı yerel tercihler global olarak tatmin edilemez (K₃ örneğinde 3 kenarın üçü birden kesilemez). QAOA'nın kuantum superposition üzerinden çalışması, bu lokal tuzaklara klasik optimizer'lardan farklı bir perspektif sunar.

**Genel tam graflar $K_n$:** MaxCut $\lfloor n^2/4 \rfloor$. Kontrol: $K_3 \to 2$, $K_4 \to 4$, $K_5 \to 6$, $K_6 \to 9$.

---

# BÖLÜM B — Ising Hamiltonian + Eigenspectrum Sezgisi

## B.1. Klasik $C(\mathbf{s})$'ten Kuantum $H_C$'ye Köprü

### B.1.a. Maksimizasyondan Minimizasyona

**Yol 1 konvansiyonu** (bizim tercihimiz, Qiskit-uyumlu):

Klasik cost'un işaretini çeviriyoruz — kuantum tarafında **ground state** (en düşük enerji) aradığımız için:

$$H_C = \frac{1}{2} \sum_{(i,j) \in E} \left( s_i s_j - 1 \right)$$

Sabit $-|E|/2$ terimi optimum noktayı kaydırmaz, genellikle ihmal edilir.

### B.1.b. Klasik $s_i$'leri Kuantum $Z_i$'lerle Değiştirme

**Eşleme:**

$$s_i \ (\text{klasik}) \ \longleftrightarrow \ Z_i \ (\text{i'inci qubit üzerinde Pauli-Z})$$

Burada $Z_i$ $n$ qubit'lik sistemin $i$'inci qubit'ine $Z$ operatörü, diğerlerine identity:

$$Z_i = \underbrace{\mathbb{1} \otimes \cdots \otimes \mathbb{1}}_{i \text{ adet}} \otimes Z \otimes \underbrace{\mathbb{1} \otimes \cdots \otimes \mathbb{1}}_{n-i-1 \text{ adet}}$$

### B.1.c. Cost Hamiltonian (Yol 1)

$$\boxed{\; H_C = \frac{1}{2} \sum_{(i,j) \in E} \left( Z_i Z_j - \mathbb{1} \right) \;}$$

### B.1.d. Neden $H_C$ Diyagonal?

$Z_i Z_j$ operatörleri tüm **computational basis state**'lerde diyagonaldir:

$$Z_i Z_j |z_0 z_1 \ldots z_{n-1}\rangle = (-1)^{z_i + z_j} |z_0 z_1 \ldots z_{n-1}\rangle$$

- $z_i = z_j$ ise $+1$
- $z_i \neq z_j$ ise $-1$

Sonuç: $H_C$'nin **her computational basis state'i bir eigenstate'tir**, karşılık gelen eigenvalue tam olarak (negatif) cost değeridir:

$$H_C |z\rangle = -C(z) |z\rangle$$

**QAOA'nın temel fikri:**

> Ground state (en düşük enerji) = en çok kenar kesen bitstring

## B.2. Eigenstate Yapısı ve Konvansiyon Seçimi

### B.2.a. İki Konvansiyon Karşılaştırması

| Konvansiyon | $H_C$ formu | Hedef | Kim kullanır |
|---|---|---|---|
| **Yol 1** | $\frac{1}{2}\sum (Z_i Z_j - \mathbb{1})$ | **Minimize** $\langle H_C \rangle$ | Qiskit, PennyLane |
| **Yol 2** | $\frac{1}{2}\sum (\mathbb{1} - Z_i Z_j)$ | **Maximize** $\langle H_C \rangle$ | Farhi 2014, orijinal paper |

### B.2.b. Bizim Seçimimiz: Yol 1

**Gerekçeler:**
1. Qiskit/implementasyon dünyasıyla uyum → kod ile sunum arasında kopukluk yok
2. Klasik optimizer'lar (SciPy COBYLA, SPSA vb.) zaten minimizer
3. Scaling deneylerinde standart optimizer çağrıları doğrudan çalışır

### B.2.c. Sunum Stratejisi

Sunumda her iki konvansiyondan da kısaca bahsedilecek, Yol 1 tercihi açıkça deklare edilecek. Bu:
- İki literatür konvansiyonunu dinleyiciye tanıtır
- Bilinçli bir tasarım seçimi yaptığımızı gösterir
- Referans setimizin #1 kaynağı (Farhi 2014) ile #7 (Qiskit docs) arasındaki farkı açıklar

### B.2.d. Eigenspectrum Sezgisi (Yol 1'de)

- $H_C$'nin her **computational basis state'i** ($2^n$ tane) bir eigenstate
- Eigenvalue = $-C(z)$ (negatif cost)
- **Optimal cut ↔ Ground state** (en negatif eigenvalue)

**QAOA'nın yapmak istediği:**

Başlangıçta tüm $2^n$ basis state'leri eşit olasılıkla içeren uniform superposition:

$$|\psi_0\rangle = H^{\otimes n} |0\rangle^{\otimes n} = \frac{1}{\sqrt{2^n}} \sum_{z \in \{0,1\}^n} |z\rangle$$

Sonra parametreli operasyonlarla bu superposition'ı **eviriştir** ki olasılık kütlesi optimal bitstring'lerin üzerinde yoğunlaşsın. "Evriltme" işini **cost operator** $U_C(\gamma) = e^{-i\gamma H_C}$ ve **mixer operator** $U_B(\beta) = e^{-i\beta H_B}$ yapar (Faz 2.2'nin konusu).

## B.3. K₃ Üçgen Örneğinin Tam Spektrumu

Yol 1 konvansiyonu:

$$H_C = \frac{1}{2}\left[ (Z_0 Z_1 - \mathbb{1}) + (Z_1 Z_2 - \mathbb{1}) + (Z_0 Z_2 - \mathbb{1}) \right]$$

$$= \frac{1}{2}(Z_0 Z_1 + Z_1 Z_2 + Z_0 Z_2) - \frac{3}{2}\mathbb{1}$$

### B.3.a. 8 Basis State için Eigenvalue

| Bitstring $\|z_0 z_1 z_2\rangle$ | Cost $C(z)$ | Eigenvalue $-C(z)$ |
|---|---|---|
| $\|000\rangle$ | 0 | **0** |
| $\|001\rangle$ | 2 | **−2** (ground) |
| $\|010\rangle$ | 2 | **−2** (ground) |
| $\|011\rangle$ | 2 | **−2** (ground) |
| $\|100\rangle$ | 2 | **−2** (ground) |
| $\|101\rangle$ | 2 | **−2** (ground) |
| $\|110\rangle$ | 2 | **−2** (ground) |
| $\|111\rangle$ | 0 | **0** |

### B.3.b. Spektrum Yapısı

$H_C$'nin spektrumu sadece **iki farklı eigenvalue**:

$$\text{spec}(H_C) = \{-2, 0\}$$

**Dejenerasyon:**
- **Eigenvalue −2 (ground state):** 6 basis state — MaxCut'ın optimal çözümleri
- **Eigenvalue 0:** $|000\rangle$ ve $|111\rangle$ — "her düğüm aynı kümede" konfigürasyonları

### B.3.c. Uniform Superposition Baseline

$P(|z\rangle) = 1/8$ her basis state için. Beklenen cost:

$$\langle \psi_0 | H_C | \psi_0 \rangle = \frac{1}{8}(0 + (-2) \cdot 6 + 0) = -\frac{12}{8} = -1.5$$

**Approximation ratio** tanımı (Yol 1'de):

$$r = \frac{-\langle H_C \rangle}{C^*}$$

- Uniform superposition (K₃): $r = 1.5 / 2 = 0.75$
- Mükemmel çözüm: $r = 1.0$

### B.3.d. K₃ Özelinin Tuzağı — Önemli Sunum Notu

**K₃ çok özel bir durum:** Optimal çözümler 8 konfigürasyonun $6/8 = \%75$'ini kaplıyor. Bu nedenle rastgele örnekleme bile $r = 0.75$ verir.

**Genel graflarda durum farklı:**
- Optimal çözümler $2^n$ konfigürasyonun **ihmal edilebilir** küçük bir kısmını kaplar
- Uniform superposition'dan beklenen $r$, tipik graflar için $\approx 0.5$'e yakınsar
- Farhi'nin p=1 alt sınırı $r \geq 0.6924$ (3-regular graflar) **her $n$ için** geçerli

**Sunumda bu fark açıkça belirtilecek:** K₃'te "rastgele örnekleme zaten iyi" izlenimi vermek yerine, scaling deneylerinin (N=3..10) QAOA'nın değerinin büyük graflarda ortaya çıktığını gösterdiğini vurgulayacağız. Bu, **Complexity & Resource Analysis (15 puan)** slaytlarının hikâyesini doğrudan güçlendirir.

## B.4. Kritik İçgörü — Cost Operatörünün Tek Başına Yetmemesi

**Önemli gözlem:** $H_C$ sadece $Z$ ve $\mathbb{1}$ operatörlerinden oluşur. Bu da şu anlama gelir:

$$e^{-i\gamma H_C} |z\rangle = e^{-i\gamma (-C(z))} |z\rangle = e^{i\gamma C(z)} |z\rangle$$

Her basis state kendine kalır, sadece önüne bir **kompleks faz** gelir. Bu "diagonal unitary" demek — $U_C$ tek başına **basis state'ler arasında karışma yaratamaz**.

**Sonuç:** Uniform superposition'dan başlayıp sadece $U_C(\gamma)$ uygularsan, her basis state'in genliğinin sadece fazı değişir — **olasılık dağılımı (mutlak değer kareleri) aynı kalır**.

Bu boşluğu kapatmak için **mixer operatörü** $U_B(\beta) = e^{-i\beta H_B}$ lazım, ve bu operatör $X$ tabanlı olmalı. $X$ operatörü $Z$ basis'inde diyagonal olmadığı için basis state'ler arasında karışma yaratır. **Faz 2.2'nin temel motivasyonu budur.**

---

# Özet — Faz 2.1'den Çıkan Eldeki Taşlar

1. ✅ Klasik MaxCut formülasyonu (binary ve spin formu)
2. ✅ K₃ için klasik enumerasyon: $C^* = 2$, 6 optimal çözüm
3. ✅ Spin → Pauli-Z eşlemesi
4. ✅ Cost Hamiltonian: $H_C = \frac{1}{2}\sum_{(i,j)\in E}(Z_i Z_j - \mathbb{1})$ (Yol 1)
5. ✅ $H_C$'nin diyagonal yapısı: her bitstring bir eigenstate, eigenvalue = negatif cost
6. ✅ K₃ spektrumu: $\{-2, 0\}$, ground state 6 kat dejenere
7. ✅ Uniform superposition baseline: $r = 0.75$ (K₃ özelinde)
8. ✅ Konvansiyon seçimi: Yol 1 (Qiskit-uyumlu), sunumda Yol 2'den de bahsedilecek
9. ✅ Kritik içgörü: $U_C$ tek başına olasılık dağılımını değiştiremez → mixer gerekli

---

# Sırada: Faz 2.2 — QAOA Ansatz Anatomisi

- **A.** Initial state hazırlığı: $H^{\otimes n}|0\rangle^{\otimes n}$ neden?
- **B.** Cost operator $U_C(\gamma) = e^{-i\gamma H_C}$ — devre karşılığı (hocanın $R_z$ türetmesine bağlantı)
- **C.** Mixer operator $U_B(\beta) = e^{-i\beta H_B}$ — neden $X$ tabanlı?
- **D.** p-layer yapısı ve adiabatic connection önizlemesi
