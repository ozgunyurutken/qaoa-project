"""
Module 4 — metrics.

All quantities needed to evaluate a QAOA run:

    expectation_value(qc, H)                 — exact <ψ|H|ψ> via Statevector
    approximation_ratio(expectation, C*)     — r = -<H_C> / C*  (Option 1)
    gate_count(qc, transpiled=True)          — {"total", "cnot", "single_qubit", "depth"}
    measurement_histogram(qc, n_shots)       — bitstring → probability (V2 sampler)

Notes
-----
* `expectation_value` is *exact* (no sampling noise). The scaling study uses
  Statevector, not shot-based estimation, so we keep that path explicit.
* `gate_count(qc, transpiled=True)` runs `transpile_circuit` internally before
  counting, so the caller can pass the raw ansatz and get the final basis-
  aligned counts.
* `measurement_histogram` uses Qiskit 2.x V2 primitive `StatevectorSampler`.
"""
from __future__ import annotations

from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.quantum_info import SparsePauliOp, Statevector

from src.circuit import transpile_circuit


# ---------------------------------------------------------------------------
# Exact expectation value
# ---------------------------------------------------------------------------

def expectation_value(qc: QuantumCircuit, hamiltonian: SparsePauliOp) -> float:
    """
    Exact <ψ|H|ψ> via `Statevector(qc).expectation_value(H)`.

    Returns the real part (the Hamiltonians we build are Hermitian, so the
    imaginary part is zero up to floating-point noise).
    """
    sv = Statevector(qc)
    return float(sv.expectation_value(hamiltonian).real)


# ---------------------------------------------------------------------------
# Approximation ratio (Option 1 convention)
# ---------------------------------------------------------------------------

def approximation_ratio(expectation_hc: float, optimal_cut: int) -> float:
    """
    r = -<H_C> / C*

    With Option 1 (H_C eigenvalues = -C(z)), the expectation is non-positive
    and C* ≥ 1 for any graph with at least one edge, so r ∈ [0, 1] for any
    physical state.
    """
    if optimal_cut <= 0:
        raise ValueError(
            f"optimal_cut must be >= 1 (edgeless graphs have trivial r), got {optimal_cut}"
        )
    return -expectation_hc / optimal_cut


# ---------------------------------------------------------------------------
# Gate count
# ---------------------------------------------------------------------------

def gate_count(qc: QuantumCircuit, transpiled: bool = True) -> dict:
    """
    Count gates on the circuit.

    Parameters
    ----------
    qc
        A QAOA circuit (concrete or parametric).
    transpiled
        If True, transpile to the fixed basis {cx, rz, rx, h} first so the
        returned counts match the ones actually executed. If False, count
        the raw ansatz gates (Rzz would still be expressed as CX—Rz—CX by
        our builder, so in practice the two paths agree for this project).

    Returns
    -------
    dict with keys "total", "cnot", "single_qubit", "depth".
    """
    circuit = transpile_circuit(qc) if transpiled else qc
    ops = circuit.count_ops()
    cnot = ops.get("cx", 0)
    total = sum(ops.values())
    return {
        "total": int(total),
        "cnot": int(cnot),
        "single_qubit": int(total - cnot),
        "depth": int(circuit.depth()),
    }


# ---------------------------------------------------------------------------
# Measurement histogram (sampling)
# ---------------------------------------------------------------------------

def measurement_histogram(qc: QuantumCircuit, n_shots: int = 10_000) -> dict:
    """
    Sample `n_shots` measurements and return a bitstring → probability dict.

    Bitstrings follow Qiskit's little-endian convention (rightmost char =
    qubit 0). If the circuit has no classical register yet, `measure_all`
    is added on a copy; the caller's circuit is not mutated.
    """
    if n_shots < 1:
        raise ValueError(f"n_shots must be >= 1, got {n_shots}")

    qc_meas = qc.copy()
    if qc_meas.num_clbits == 0:
        qc_meas.measure_all()

    sampler = StatevectorSampler()
    job = sampler.run([qc_meas], shots=n_shots)
    pub_result = job.result()[0]

    # The measurement register is named "meas" when `measure_all` is used;
    # otherwise take the first BitArray-valued field on DataBin.
    data_bin = pub_result.data
    if hasattr(data_bin, "meas"):
        bit_array = data_bin.meas
    else:
        # Pick the single BitArray field programmatically.
        fields = [name for name in data_bin if hasattr(getattr(data_bin, name), "get_counts")]
        if not fields:
            raise RuntimeError("No BitArray field found on sampler result DataBin.")
        bit_array = getattr(data_bin, fields[0])

    counts = bit_array.get_counts()
    return {bitstring: count / n_shots for bitstring, count in counts.items()}


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import numpy as np

    from src.circuit import qaoa_circuit
    from src.graph_generator import generate_3regular_graph, generate_triangle
    from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value

    print("=" * 60)
    print("Module 4 demo — metrics")
    print("=" * 60)

    K3 = generate_triangle()
    H_K3 = build_cost_hamiltonian(K3)
    C_star_K3 = optimal_cut_value(K3)

    print("\n[1] Uniform superposition on K₃  (|+⟩⊗3):")
    qc_plus = QuantumCircuit(3)
    qc_plus.h(range(3))
    ev_plus = expectation_value(qc_plus, H_K3)
    r_plus = approximation_ratio(ev_plus, C_star_K3)
    print(f"    <H_C>   = {ev_plus:+.6f}   (expected -1.5)")
    print(f"    ratio r = {r_plus:.6f}    (expected 0.75)")

    print("\n[2] Optimal basis state |001⟩ on K₃:")
    sv_opt = Statevector.from_label("001")
    ev_opt = float(sv_opt.expectation_value(H_K3).real)
    r_opt = approximation_ratio(ev_opt, C_star_K3)
    print(f"    <H_C>   = {ev_opt:+.6f}   (expected -2.0)")
    print(f"    ratio r = {r_opt:.6f}    (expected 1.0)")

    print("\n[3] QAOA K₃ p=1 (γ=0.3, β=0.2) — random parameters, not optimised:")
    qc1 = qaoa_circuit(K3, p=1, gammas=[0.3], betas=[0.2])
    ev1 = expectation_value(qc1, H_K3)
    r1 = approximation_ratio(ev1, C_star_K3)
    print(f"    <H_C>   = {ev1:+.6f}")
    print(f"    ratio r = {r1:.6f}    (should be between 0.5 and 1.0)")

    print("\n[4] Gate count on K₃ QAOA p=2 (transpiled):")
    qc2 = qaoa_circuit(K3, p=2, gammas=[0.3, 0.5], betas=[0.2, 0.4])
    gc = gate_count(qc2, transpiled=True)
    print(f"    {gc}")
    print(f"    (expected cnot=12 = 2·|E|·p)")

    print("\n[5] Gate count vs N and p (3-regular, seed=0, transpiled):")
    print(f"    {'n':>3} {'p':>3}  {'total':>6} {'cnot':>5} {'1q':>5} {'depth':>6}")
    for n in (4, 6, 8, 10):
        for p in (1, 2, 3):
            G = generate_3regular_graph(n, seed=0)
            qc = qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p)
            g = gate_count(qc, transpiled=True)
            print(f"    {n:>3} {p:>3}  {g['total']:>6} {g['cnot']:>5} "
                  f"{g['single_qubit']:>5} {g['depth']:>6}")

    print("\n[6] Measurement histogram for |+⟩⊗3 (10000 shots):")
    hist = measurement_histogram(qc_plus, n_shots=10_000)
    total = sum(hist.values())
    print(f"    keys = {sorted(hist.keys())}")
    print(f"    sample probs = {[round(hist[k], 3) for k in sorted(hist.keys())]}")
    print(f"    sum = {total:.6f}  (expected 1.0)")
    print(f"    max deviation from 1/8 = {max(abs(p - 1/8) for p in hist.values()):.4f}")

    print("\n[7] Histogram for optimised QAOA circuit approximation (γ=0.3, β=0.2):")
    hist2 = measurement_histogram(qc1, n_shots=10_000)
    items = sorted(hist2.items(), key=lambda kv: -kv[1])
    print(f"    top 4: {[(k, round(v, 3)) for k, v in items[:4]]}")
    print(f"    sum   = {sum(hist2.values()):.6f}")
