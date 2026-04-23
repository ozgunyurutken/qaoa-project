"""Tests for Module 3: circuit."""
from __future__ import annotations

import networkx as nx
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from src.circuit import (
    cost_layer,
    mixer_layer,
    qaoa_circuit,
    qaoa_circuit_parametric,
    transpile_circuit,
)
from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import build_cost_hamiltonian


def _cx(qc: QuantumCircuit) -> int:
    return qc.count_ops().get("cx", 0)


# ---------------------------------------------------------------------------
# CNOT counts (brief Section 3.2 ground truths)
# ---------------------------------------------------------------------------

def test_k3_p1_cnot_count():
    """K3, p=1 => exactly 2*|E|*p = 2*3*1 = 6 CNOTs."""
    qc = qaoa_circuit(generate_triangle(), p=1, gammas=[0.3], betas=[0.4])
    assert _cx(qc) == 6


def test_k3_p2_cnot_count():
    """K3, p=2 => exactly 2*|E|*p = 2*3*2 = 12 CNOTs."""
    qc = qaoa_circuit(generate_triangle(), p=2, gammas=[0.1, 0.2], betas=[0.3, 0.4])
    assert _cx(qc) == 12


@pytest.mark.parametrize("n,p", [(4, 1), (4, 2), (6, 1), (6, 2), (8, 3), (10, 3)])
def test_3regular_cnot_count_formula(n: int, p: int):
    """3-regular: 2*|E|*p CNOTs. |E| = 3n/2 so expected = 3*n*p."""
    G = generate_3regular_graph(n, seed=0)
    qc = qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p)
    assert _cx(qc) == 2 * G.number_of_edges() * p == 3 * n * p


# ---------------------------------------------------------------------------
# Circuit depth scaling
# ---------------------------------------------------------------------------

def test_depth_strictly_increases_with_p():
    """Adding a layer must strictly increase circuit depth."""
    G = generate_3regular_graph(6, seed=0)
    depths = [
        qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p).depth()
        for p in range(1, 5)
    ]
    for a, b in zip(depths, depths[1:]):
        assert b > a, f"depth not monotonic: {depths}"


def test_depth_linear_in_p():
    """First differences of depth(p) should be (nearly) constant."""
    G = generate_3regular_graph(6, seed=0)
    depths = [
        qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p).depth()
        for p in range(1, 5)
    ]
    diffs = [b - a for a, b in zip(depths, depths[1:])]
    # Every layer adds the same sub-circuit, so diffs must all be equal.
    assert max(diffs) - min(diffs) <= 1, f"per-layer depth not constant: diffs={diffs}"


# ---------------------------------------------------------------------------
# Parameter count (parametric variant)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("p", [1, 2, 3])
def test_parameter_count_equals_2p(p: int):
    qc, gammas, betas = qaoa_circuit_parametric(generate_triangle(), p=p)
    assert qc.num_parameters == 2 * p
    assert len(gammas) == p and len(betas) == p


def test_parametric_bind_matches_concrete():
    """Binding the parametric circuit matches the concrete build exactly."""
    G = generate_triangle()
    gs = [0.3, 0.5]
    bs = [0.2, 0.4]

    qc_p, gparams, bparams = qaoa_circuit_parametric(G, p=2)
    binding = dict(zip(list(gparams) + list(bparams), gs + bs))
    qc_bound = qc_p.assign_parameters(binding)

    qc_c = qaoa_circuit(G, p=2, gammas=gs, betas=bs)

    np.testing.assert_allclose(
        Statevector(qc_bound).data, Statevector(qc_c).data, atol=1e-12
    )


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_p1_zero_parameters_gives_uniform_superposition():
    """p=1 with γ=β=0 reduces to H⊗n (since U_C(0)=U_B(0)=I).

    Expected: probabilities = 1/2^n for every basis state.
    """
    n = 3
    qc = qaoa_circuit(generate_triangle(), p=1, gammas=[0.0], betas=[0.0])
    sv = Statevector(qc)
    probs = np.abs(sv.data) ** 2
    np.testing.assert_allclose(probs, [1.0 / 2**n] * 2**n, atol=1e-12)


def test_h_only_gives_uniform_superposition_k3():
    """Direct: H^n |0>^n has all amplitudes equal to 1/sqrt(2^n)."""
    n = 3
    qc = QuantumCircuit(n)
    qc.h(range(n))
    sv = Statevector(qc)
    assert np.allclose(np.abs(sv.data), 1.0 / np.sqrt(2**n))


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_p_zero_raises():
    with pytest.raises(ValueError, match="p must be >= 1"):
        qaoa_circuit(generate_triangle(), p=0, gammas=[], betas=[])


def test_param_length_mismatch_raises():
    with pytest.raises(ValueError, match="Expected p"):
        qaoa_circuit(generate_triangle(), p=2, gammas=[0.1], betas=[0.2, 0.3])


# ---------------------------------------------------------------------------
# Transpile behaviour
# ---------------------------------------------------------------------------

def test_transpile_preserves_expectation():
    """Transpilation is unitary-preserving: <ψ|H_C|ψ> is invariant."""
    G = generate_triangle()
    H = build_cost_hamiltonian(G)
    qc = qaoa_circuit(G, p=2, gammas=[0.3, 0.5], betas=[0.2, 0.4])

    ev_raw = Statevector(qc).expectation_value(H).real
    ev_t = Statevector(transpile_circuit(qc, optimization_level=2)).expectation_value(H).real

    assert np.isclose(ev_raw, ev_t, atol=1e-10)


def test_transpile_does_not_increase_cnot():
    """Level-2 transpilation must not add CNOTs (may reduce / keep same)."""
    G = generate_triangle()
    qc = qaoa_circuit(G, p=2, gammas=[0.1, 0.2], betas=[0.3, 0.4])
    before = _cx(qc)
    after = _cx(transpile_circuit(qc, optimization_level=2))
    assert after <= before


# ---------------------------------------------------------------------------
# Layer helpers applied directly
# ---------------------------------------------------------------------------

def test_cost_layer_gate_count_matches_edges():
    """cost_layer adds 2 CX + 1 Rz per edge."""
    G = generate_3regular_graph(6, seed=0)
    qc = QuantumCircuit(G.number_of_nodes())
    cost_layer(qc, G, gamma=0.1)
    ops = qc.count_ops()
    assert ops.get("cx", 0) == 2 * G.number_of_edges()
    assert ops.get("rz", 0) == G.number_of_edges()


def test_mixer_layer_gate_count_matches_qubits():
    """mixer_layer adds exactly n Rx gates."""
    qc = QuantumCircuit(5)
    mixer_layer(qc, n=5, beta=0.2)
    ops = qc.count_ops()
    assert ops.get("rx", 0) == 5
