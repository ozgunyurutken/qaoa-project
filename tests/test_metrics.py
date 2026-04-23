"""Tests for Module 4: metrics."""
from __future__ import annotations

import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from src.circuit import qaoa_circuit
from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value
from src.metrics import (
    approximation_ratio,
    expectation_value,
    gate_count,
    measurement_histogram,
)


# ---------------------------------------------------------------------------
# Brief Section 3.2 named tests
# ---------------------------------------------------------------------------

def test_uniform_superposition_k3_ratio():
    """r(|+⟩^3, K₃) = 0.75.

    <H_C> on uniform = mean of eigenvalues = (6·(-2) + 2·0)/8 = -1.5.
    C* = 2, so r = -(-1.5)/2 = 0.75.
    """
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    qc = QuantumCircuit(3)
    qc.h(range(3))

    ev = expectation_value(qc, H)
    assert np.isclose(ev, -1.5, atol=1e-12)

    r = approximation_ratio(ev, optimal_cut_value(K3))
    assert np.isclose(r, 0.75, atol=1e-12)


def test_optimal_state_k3_ratio():
    """r(|001⟩, K₃) = 1.0.

    |001⟩ is one of the six optimal basis states for K₃ (cut = 2 ⇒ energy = -2).
    """
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    sv = Statevector.from_label("001")
    # Use expectation_value directly on the Statevector (circuit path works too).
    ev = float(sv.expectation_value(H).real)
    assert np.isclose(ev, -2.0, atol=1e-12)

    r = approximation_ratio(ev, optimal_cut_value(K3))
    assert np.isclose(r, 1.0, atol=1e-12)


def test_gate_count_correctness():
    """Transpiled gate counts match expected for QAOA on K₃ and 3-regular n=6."""
    # K₃, p=1: 2·|E|·p = 6 CNOTs. Singles per layer: 3 Rz + 3 Rx + 3 H (initial)
    K3 = generate_triangle()
    qc = qaoa_circuit(K3, p=1, gammas=[0.3], betas=[0.2])
    gc = gate_count(qc, transpiled=True)
    assert gc["cnot"] == 6
    assert gc["single_qubit"] == 3 + 3 + 3  # Rz + Rx + initial H
    assert gc["total"] == gc["cnot"] + gc["single_qubit"]
    assert gc["depth"] == qc.depth() or gc["depth"] > 0  # depth is positive

    # 3-reg n=6, p=2: 2·|E|·p = 36 CNOTs.
    # Per layer singles: |E| Rz + n Rx = 9 + 6 = 15.  Plus initial n H = 6.
    # Total singles = p·15 + 6 = 2·15 + 6 = 36.
    G = generate_3regular_graph(6, seed=0)
    qc6 = qaoa_circuit(G, p=2, gammas=[0.1, 0.2], betas=[0.3, 0.4])
    gc6 = gate_count(qc6, transpiled=True)
    assert gc6["cnot"] == 36
    assert gc6["single_qubit"] == 2 * (9 + 6) + 6
    assert gc6["total"] == gc6["cnot"] + gc6["single_qubit"]


def test_histogram_normalization():
    """Sampled probabilities sum to 1.0 ± floating-point tolerance."""
    G = generate_3regular_graph(4, seed=0)
    qc = qaoa_circuit(G, p=1, gammas=[0.3], betas=[0.2])
    hist = measurement_histogram(qc, n_shots=5_000)
    assert np.isclose(sum(hist.values()), 1.0, atol=1e-9)


# ---------------------------------------------------------------------------
# expectation_value — extra ground truths
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "bitstring,expected_energy",
    [
        ("000", 0.0),   # cut = 0 edges
        ("001", -2.0),  # cut = 2 (optimal)
        ("010", -2.0),
        ("100", -2.0),
        ("011", -2.0),
        ("101", -2.0),
        ("110", -2.0),
        ("111", 0.0),
    ],
)
def test_expectation_value_on_every_k3_basis_state(bitstring, expected_energy):
    """<z|H_C|z> = -C(z) for every basis state on K₃ (Option 1 bijection)."""
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    qc = QuantumCircuit(3)
    # State |bitstring> in little-endian — flip qubit i iff char at position n-1-i is '1'.
    n = 3
    for i in range(n):
        if bitstring[n - 1 - i] == "1":
            qc.x(i)
    ev = expectation_value(qc, H)
    assert np.isclose(ev, expected_energy, atol=1e-12)


def test_expectation_value_is_real():
    """Hermitian H ⇒ expectation is real (we cast to float explicitly)."""
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    qc = qaoa_circuit(K3, p=2, gammas=[0.3, 0.5], betas=[0.2, 0.4])
    ev = expectation_value(qc, H)
    assert isinstance(ev, float)


# ---------------------------------------------------------------------------
# approximation_ratio — edge cases and range
# ---------------------------------------------------------------------------

def test_approximation_ratio_formula():
    """r = -<H_C>/C* — direct arithmetic check."""
    assert approximation_ratio(-1.5, 2) == 0.75
    assert approximation_ratio(-2.0, 2) == 1.0
    assert approximation_ratio(0.0, 2) == 0.0


def test_approximation_ratio_optimal_cut_zero_raises():
    with pytest.raises(ValueError, match="optimal_cut must be >= 1"):
        approximation_ratio(-1.0, 0)


def test_approximation_ratio_qaoa_within_bounds():
    """For any quantum state and any graph, 0 ≤ r ≤ 1 under Option 1."""
    G = generate_3regular_graph(6, seed=0)
    H = build_cost_hamiltonian(G)
    C_star = optimal_cut_value(G)
    # Try a few random-ish QAOA parameter settings.
    for gammas, betas in [([0.1], [0.2]), ([0.3, 0.5], [0.2, 0.4]), ([1.0, 0.5, 0.3], [0.4, 0.2, 0.1])]:
        qc = qaoa_circuit(G, p=len(gammas), gammas=gammas, betas=betas)
        ev = expectation_value(qc, H)
        r = approximation_ratio(ev, C_star)
        assert 0.0 <= r <= 1.0 + 1e-9, f"ratio out of range: {r}"


# ---------------------------------------------------------------------------
# gate_count — 3-regular scaling (2·|E|·p CNOT formula)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n,p", [(4, 1), (6, 2), (8, 3), (10, 1)])
def test_gate_count_cnot_formula_3regular(n, p):
    G = generate_3regular_graph(n, seed=0)
    qc = qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p)
    gc = gate_count(qc, transpiled=True)
    assert gc["cnot"] == 2 * G.number_of_edges() * p == 3 * n * p


def test_gate_count_keys():
    """gate_count returns exactly the brief's keys."""
    qc = qaoa_circuit(generate_triangle(), p=1, gammas=[0.3], betas=[0.2])
    gc = gate_count(qc)
    assert set(gc.keys()) == {"total", "cnot", "single_qubit", "depth"}
    for v in gc.values():
        assert isinstance(v, int)


def test_gate_count_total_equals_cnot_plus_single():
    """After transpile to {cx, rz, rx, h}, total = cnot + single_qubit exactly."""
    G = generate_3regular_graph(8, seed=0)
    qc = qaoa_circuit(G, p=3, gammas=[0.1] * 3, betas=[0.2] * 3)
    gc = gate_count(qc, transpiled=True)
    assert gc["total"] == gc["cnot"] + gc["single_qubit"]


# ---------------------------------------------------------------------------
# measurement_histogram — shape and content
# ---------------------------------------------------------------------------

def test_histogram_uniform_superposition_roughly_uniform():
    """|+⟩^3 should give 8 keys each with p ≈ 1/8. Allow statistical slack."""
    qc = QuantumCircuit(3)
    qc.h(range(3))
    hist = measurement_histogram(qc, n_shots=20_000)
    assert len(hist) == 8
    for p in hist.values():
        assert abs(p - 1 / 8) < 0.02  # ~1.4σ bound at n=20k, generous


def test_histogram_basis_state_is_deterministic():
    """X|0⟩⊗|00⟩ on qubit 0 should produce only '001' (little-endian)."""
    qc = QuantumCircuit(3)
    qc.x(0)
    hist = measurement_histogram(qc, n_shots=500)
    assert set(hist.keys()) == {"001"}
    assert np.isclose(hist["001"], 1.0)


def test_histogram_keys_are_binary_strings_of_correct_length():
    G = generate_3regular_graph(4, seed=0)
    qc = qaoa_circuit(G, p=1, gammas=[0.3], betas=[0.2])
    hist = measurement_histogram(qc, n_shots=1_000)
    for key in hist:
        assert isinstance(key, str)
        assert len(key) == 4
        assert all(c in "01" for c in key)


def test_histogram_n_shots_zero_raises():
    qc = QuantumCircuit(2)
    qc.h(range(2))
    with pytest.raises(ValueError, match="n_shots must be >= 1"):
        measurement_histogram(qc, n_shots=0)


def test_histogram_does_not_mutate_input_circuit():
    """measurement_histogram must not add classical bits to the caller's circuit."""
    qc = QuantumCircuit(2)
    qc.h(range(2))
    clbits_before = qc.num_clbits
    _ = measurement_histogram(qc, n_shots=100)
    assert qc.num_clbits == clbits_before
