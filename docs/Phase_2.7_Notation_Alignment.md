# Faz 2.7 — Hocanın Notasyonuyla Son Hizalama

**Ders:** BBL540E — Quantum Data Structures & Algorithms
**Hoca:** Doç. Dr. Deniz Türkpençe
**Tarih:** Nisan 2026
**Durum:** %100 Tamamlandı — **Faz 2 kapanış dokümanı**

---

## İçerik Haritası

- **Bölüm A:** Hocanın notasyon envanteri (QDW1-6'dan)
- **Bölüm B:** Bizim fazlarımızda kullandığımız notasyon — uyum değerlendirmesi
- **Bölüm C:** Potansiyel karışıklık noktaları ve çözümleri
- **Bölüm D:** Hocanın pedagojik tarzı (sunumda uygulanmayacak — karar verildi)
- **Bölüm E:** Faz 2 için notasyon konsolidasyonu (kesin sunum notasyonu)
- **Bölüm F:** Disclaimer ve notation bridge kararları

Bu faz kavramsal yük getirmiyor — Faz 2.1-2.6'da oluşan notasyonu hocanın framework'üyle hizalıyor ve sunum için kesin gösterim seti belirliyor.

---

# BÖLÜM A — Hocanın Notasyon Envanteri

## A.1. Temel Gösterim

| Kavram | Hocanın Notasyonu | Kaynak |
|---|---|---|
| Ket vektörü | $\|\psi\rangle, \|\alpha\rangle$ | QDW1 |
| Bra vektörü | $\langle\psi\|, \langle\alpha\|$ | QDW1 |
| Iç çarpım | $\langle\alpha\|\beta\rangle$ | QDW1 |
| Dış çarpım | $\|\psi\rangle\langle\phi\|$ | QDW2 |
| Identity | $\mathbb{1}$ (çift-çizgi) | QDW1 |
| Null operator | $\mathbb{N}$ | QDW1 |
| Lineer operatör | $\hat{A}$ veya $A$ | QDW1 |
| Adjoint | $A^\dagger$ | QDW2 |

## A.2. Pauli Operatörleri

| Notasyon | Kullanım |
|---|---|
| $X \equiv \sigma_x$ | Eşdeğer, birlikte kullanılıyor |
| $Y \equiv \sigma_y$ | Eşdeğer |
| $Z \equiv \sigma_z$ | Eşdeğer |

## A.3. Gate'ler (QDW2-3)

| Gate | Tanım |
|---|---|
| Hadamard | $H = \frac{1}{\sqrt{2}}\begin{pmatrix}1 & 1 \\ 1 & -1\end{pmatrix}$ |
| $R_x(\theta)$ | $e^{-i\frac{\theta}{2}\sigma_x}$ |
| $R_y(\theta)$ | $e^{-i\frac{\theta}{2}\sigma_y}$ |
| $R_z(\theta)$ | $e^{-i\frac{\theta}{2}\sigma_z}$ |
| Arbitrary | $R_{\mathbf{n}}(\theta) = e^{-i\frac{\theta}{2}\mathbf{n}\cdot\boldsymbol{\sigma}}$ |

**Kritik uyum:** Hocanın tüm rotasyon gate'leri **$\theta/2$ açılı eksponansiyel** formda — QAOA cost operatörünün formuyla birebir uyumlu.

## A.4. Expectation Value (QDW3 eq. 53)

$$\langle A \rangle = \langle\psi|A|\psi\rangle = \sum_i a_i P(a_i)$$

QAOA objective $F_p = \langle\psi_p|H_C|\psi_p\rangle$ aynı form.

## A.5. Hermitian, Unitary, Normal

- Hermitian: $A = A^\dagger$
- Unitary: $U^\dagger U = UU^\dagger = \mathbb{1}$
- Normal: $AA^\dagger = A^\dagger A$

## A.6. Spektral Ayrışım (QDW2 eq. 45)

$$M = \sum_i \lambda_i |i\rangle\langle i|$$

Örnek: $Z = |0\rangle\langle 0| - |1\rangle\langle 1|$ — QAOA cost Hamiltonian'ının temeli.

## A.7. CNOT (QDW4)

$$\text{CNOT} = |0\rangle\langle 0| \otimes \mathbb{1} + |1\rangle\langle 1| \otimes X$$

$R_{ZZ}$ ayrıştırmasındaki CNOT'lar uyumlu.

---

# BÖLÜM B — Bizim Notasyonumuz vs Hoca

| Kavram | Bizim | Hocayla Uyum |
|---|---|---|
| Computational basis | $\|z\rangle$ | ✓ |
| Pauli $Z_i$ | $Z_i$ | ✓ |
| Identity | $\mathbb{1}$ | ✓ |
| Cost Hamiltonian | $H_C$ | ✓ standart |
| Mixer Hamiltonian | $H_B$ | ✓ standart |
| Parameters | $\gamma_k, \beta_k$ | ✓ standart |
| QAOA state | $\|\psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle$ | ✓ |
| Expectation | $\langle\psi_p\|H_C\|\psi_p\rangle$ | ✓ aynı form |
| Approximation ratio | $r$ | ✓ standart |

**Değerlendirme: %100 uyumlu.** Başından itibaren hocanın framework'ünü temel aldığımız için notasyon çatışması yok.

---

# BÖLÜM C — Karışıklık Noktaları ve Çözümler

## C.1. $R_x$ vs $e^{-i\beta X}$

**Hoca:** $R_x(\theta) = e^{-i\frac{\theta}{2}\sigma_x}$
**QAOA standart:** $U_B(\beta) = e^{-i\beta X}$
**İlişki:** $U_B(\beta) = R_x(2\beta)$

**Sunum kararı:** QAOA standart formu ana notasyon, parantez içinde hocanın formuna köprü:

> "Mixer operator: $U_B(\beta) = e^{-i\beta X_i}$ — lecture notation: $R_x(2\beta)$"

## C.2. $H$ (Hadamard) vs $H$ (Hamiltonian)

**Sunum kuralı:**
- Hadamard: standalone $H$ (sadece initial state slide'ında)
- Hamiltonian: her zaman subscript ($H_C, H_B$)

Hiç "sadece $H$" yazmayacağız bir Hamiltonian için.

## C.3. $\gamma$ İşareti (Yol 1 vs Yol 2)

**Yol 1 seçimi** (Faz 2.1'de kilitlendi): negatif $H_C$, minimizasyon.
- Farhi 2014 (Yol 2): $\gamma^* > 0$
- Bizim (Yol 1): $\gamma^* < 0$

**Sunum kararı — Disclaimer YERİ:**

Disclaimer Slayt 3 (I/O & Encoding) altında tek satır altbilgi olarak eklenecek:

> *"Convention: $H_C$ in minimization form (Qiskit-compatible); Farhi 2014 uses opposite sign."*

**Neden Slayt 3?** $H_C$ ilk kez burada tanıtılıyor. Slayt 4 zaten yoğun (cost/mixer/döngü/parametreler) — disclaimer orada kaybolur.

## C.4. $s_i = 1 - 2x_i$ Konvansiyonu

**Bizim:** $x_i = 0 \leftrightarrow s_i = +1$
**Alternatif (bazı literatür):** $s_i = 2x_i - 1$

**Sunum kararı:** Slayt 3'teki eşleme tablosu ile iletilecek:

| $x_i$ | $s_i$ | Anlam |
|---|---|---|
| 0 | +1 | $i \in S$ |
| 1 | -1 | $i \notin S$ |

Yazılı açıklama gerekmez.

---

# BÖLÜM D — Pedagojik Tarz (Karar: Uygulanmayacak)

**Karar:** Hocanın "Definition → Properties → Example → YOU TRY" pedagojik kalıbı bu sunumda uygulanmayacak.

**Gerekçe:** Bu ders slaytı değil, 10-dakikalık akademik bilimsel sunum. Didaktik kalıp yerine standart akademik akış kullanılacak:

**Sunum akışı:**
1. Problem context (MaxCut)
2. Formulation (Ising encoding)
3. Method (QAOA ansatz)
4. Demonstration (K₃ toy example)
5. Results (scaling)
6. Conclusion + references

**Notasyon uyumu ise korunacak** — dinleyici tanıdık gösterim gördüğünde kavramsal yük azalır.

---

# BÖLÜM E — Kesin Sunum Notasyonu (Faz 6-7 Referansı)

## Temel Gösterim
- Ket: $|\psi\rangle$
- Bra: $\langle\psi|$
- Identity: $\mathbb{1}$
- Adjoint: $A^\dagger$
- Expectation: $\langle\psi|A|\psi\rangle$

## Pauli Operatörleri
- Tekil: $X, Y, Z$ (hocanın büyük harf tercihi)
- Indexed: $X_i, Y_i, Z_i$
- Çarpım: $Z_i Z_j$

## Gate'ler
- Hadamard: $H$ (sadece standalone)
- Rotasyonlar: $R_x(\theta), R_y(\theta), R_z(\theta)$ — hocanın $\theta/2$ formu
- Generic rotation: $R_{\mathbf{n}}(\theta)$
- CNOT: $\text{CNOT}_{c,t}$

## QAOA Spesifik
- Cost Hamiltonian: $H_C = \frac{1}{2}\sum_{(i,j)\in E}(Z_i Z_j - \mathbb{1})$ (Yol 1)
- Mixer Hamiltonian: $H_B = \sum_i X_i$
- Cost operator: $U_C(\gamma) = e^{-i\gamma H_C}$
- Mixer operator: $U_B(\beta) = e^{-i\beta H_B}$
- QAOA state: $|\psi_p(\boldsymbol{\gamma}, \boldsymbol{\beta})\rangle = \prod_{k=1}^p U_B(\beta_k)U_C(\gamma_k) \cdot H^{\otimes n}|0\rangle^{\otimes n}$
- Objective: $F_p(\boldsymbol{\gamma}, \boldsymbol{\beta}) = \langle\psi_p|H_C|\psi_p\rangle$
- Approximation ratio: $r = -\langle H_C\rangle / C^*$

## Graf ve MaxCut
- Graf: $G = (V, E)$
- Düğüm sayısı: $N$ (qubit sayısı)
- Kenar sayısı: $|E|$
- Partition: $S \subseteq V$
- Cut size: $C(S)$ veya $C(z)$
- Optimal cut: $C^*$

## Ölçüm
- Shots: $N_{\text{shots}}$
- Probability: $P(z) = |\langle z|\psi_p\rangle|^2$
- Post-selected bitstring: $z^*$

---

# BÖLÜM F — Slayt Düzenlemesi Kararları

## F.1. Notation Bridge (Slayt 4 Altbilgisi)

**Karar:** Ayrı mini-slayt yok. Slayt 4'te tek satır altbilgi:

> *"Notation follows course convention (QDW1-6)."*

Bu dinleyiciye "size yabancı gösterim yok" mesajı verir, 20 saniye kaybetmeden.

## F.2. Yol 1 Disclaimer (Slayt 3 Altbilgisi)

**Karar:** Slayt 3 altında, $H_C$'nin ilk tanıtıldığı yerde:

> *"Convention: $H_C$ in minimization form (Qiskit-compatible); Farhi 2014 uses opposite sign."*

## F.3. Genel Prensip

Sunumda **overhead bilgi minimum**: disclaimer'lar altbilgi satırı olarak, dinleyicinin akışını bozmadan.

---

# Özet — Faz 2.7'den Çıkan Eldeki Taşlar

1. ✅ Hocanın notasyon envanteri derlendi (QDW1-6)
2. ✅ Bizim notasyonumuzun %100 uyumu konfirme edildi
3. ✅ Dört potansiyel karışıklık noktası tespit edildi ve çözümlendi
4. ✅ Pedagojik tarz kararı: uygulanmayacak (akademik sunum tonu)
5. ✅ Kesin sunum notasyonu listesi kilitlendi (Faz 6-7 için referans)
6. ✅ Disclaimer yerleştirme kararları: Slayt 3 (Yol 1) + Slayt 4 (notation bridge)

---

# Faz 2 Kapanışı — %100 Tamamlandı

**Faz 2.1:** MaxCut → Ising Hamiltonian ✓
**Faz 2.2:** QAOA Ansatz Anatomy ✓
**Faz 2.3:** Adiabatic Theorem Connection ✓
**Faz 2.4:** Measurement and Approximation Ratio ✓
**Faz 2.5:** Variational Loop and Classical Optimization ✓
**Faz 2.6:** NISQ Report Card ✓
**Faz 2.7:** Notation Alignment ✓

**Faz 2 Çıktıları:**
- 7 adet .md dosyası (/mnt/user-data/outputs altında)
- Tam teorik zemin oluşturuldu
- Kesin sunum notasyonu belirlendi
- Sunum için tüm teorik içerik hazır

---

# Sırada: İmplementasyon Aşaması

Yapılacaklar:
1. Framework seçimi final (Qiskit öncelikli, alternatif değerlendirmesi)
2. Proje dosya yapısı
3. Detaylı implementasyon spesifikasyonu (N, p değerleri, metrikler, görseller)
4. Testing stratejisi
5. Beklenen çıktılar listesi

**Hedef:** İmplementasyon aşamasına geçerken hiçbir muğlaklık kalmamalı.
