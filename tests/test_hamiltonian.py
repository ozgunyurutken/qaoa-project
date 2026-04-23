"""Tests for Module 2: hamiltonian."""
from __future__ import annotations

from itertools import product

import networkx as nx
import numpy as np
import pytest
from qiskit.quantum_info import SparsePauliOp, Statevector

from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import (
    build_cost_hamiltonian,
    build_mixer_hamiltonian,
    classical_cut_value,
    optimal_cut_value,
)


# ---------------------------------------------------------------------------
# K3 reference values — the toy example the whole presentation is built on
# ---------------------------------------------------------------------------

def test_k3_hamiltonian_spectrum():
    """H_C on K3 has eigenvalues {-2 (x6), 0 (x2)} in Option 1 convention."""
    H = build_cost_hamiltonian(generate_triangle())
    eigs = np.round(np.linalg.eigvalsh(H.to_matrix()), 10)
    uniq, counts = np.unique(eigs, return_counts=True)
    assert uniq.tolist() == [-2.0, 0.0]
    assert counts.tolist() == [6, 2]


def test_k3_eigenvalue_on_001():
    """<001|H_C|001> = -C(001) = -2 (qubit 0 = 1, others 0 -> two cut edges)."""
    H = build_cost_hamiltonian(generate_triangle())
    # Statevector.from_label also uses Qiskit little-endian convention
    sv = Statevector.from_label("001")
    ev = sv.expectation_value(H).real
    assert np.isclose(ev, -2.0)


def test_k3_energy_equals_negative_cut_for_every_basis_state():
    """<z|H_C|z> = -C(z) for every computational basis state z on K3."""
    G = generate_triangle()
    H = build_cost_hamiltonian(G)
    n = G.number_of_nodes()
    for bits in product("01", repeat=n):
        bs = "".join(bits)
        expected = -classical_cut_value(bs, G)
        got = Statevector.from_label(bs).expectation_value(H).real
        assert np.isclose(got, expected), f"Mismatch for |{bs}>: got {got}, expected {expected}"


# ---------------------------------------------------------------------------
# Optimal cut values (ground truth)
# ---------------------------------------------------------------------------

def test_k3_optimal_cut():
    assert optimal_cut_value(generate_triangle()) == 2


def test_k4_optimal_cut():
    assert optimal_cut_value(nx.complete_graph(4)) == 4


@pytest.mark.parametrize("n", [3, 4, 5, 6, 7, 8])
def test_kn_optimal_cut_formula(n: int):
    """K_N optimal cut = floor(N^2 / 4) (balanced bipartition)."""
    assert optimal_cut_value(nx.complete_graph(n)) == (n * n) // 4


@pytest.mark.parametrize("n", [4, 6, 8])
def test_3regular_ground_energy_equals_neg_optimal_cut(n: int):
    """For 3-regular graphs: min eigenvalue of H_C == -C*."""
    G = generate_3regular_graph(n, seed=0)
    H = build_cost_hamiltonian(G)
    c_star = optimal_cut_value(G)
    min_eig = float(np.min(np.linalg.eigvalsh(H.to_matrix())))
    assert np.isclose(min_eig, -c_star)


# ---------------------------------------------------------------------------
# Mixer H_B
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_mixer_eigenstate_plus(n: int):
    """|+>^n is eigenstate of H_B = Σ X_i with eigenvalue n."""
    HB = build_mixer_hamiltonian(n)
    plus = Statevector.from_label("+" * n)
    ev = plus.expectation_value(HB).real
    assert np.isclose(ev, n)


def test_mixer_term_count():
    """H_B has exactly n terms, coefficient 1.0 each."""
    for n in range(1, 6):
        HB = build_mixer_hamiltonian(n)
        assert len(HB) == n
        assert all(np.isclose(c.real, 1.0) for c in HB.coeffs)


def test_mixer_n_zero_raises():
    with pytest.raises(ValueError, match="n must be >= 1"):
        build_mixer_hamiltonian(0)


# ---------------------------------------------------------------------------
# SparsePauliOp structure
# ---------------------------------------------------------------------------

def test_sparse_pauli_structure_k3():
    """K3: 3 ZZ terms (coeff +0.5 each) + 1 identity term (coeff -|E|/2 = -1.5)."""
    H = build_cost_hamiltonian(generate_triangle())
    # 3 edges + 1 identity
    assert len(H) == 4

    labels = [str(p) for p in H.paulis]
    coeffs = [c.real for c in H.coeffs]

    # Identity term
    assert "III" in labels
    identity_coeff = coeffs[labels.index("III")]
    assert np.isclose(identity_coeff, -1.5)

    # Exactly 3 ZZ terms, all with coeff +0.5
    zz_indices = [i for i, lbl in enumerate(labels) if lbl.count("Z") == 2]
    assert len(zz_indices) == 3
    assert all(np.isclose(coeffs[i], 0.5) for i in zz_indices)


@pytest.mark.parametrize("n", [4, 6, 8])
def test_sparse_pauli_structure_3regular(n: int):
    """3-regular: |E| ZZ terms + 1 identity term, |E| = 3n/2."""
    G = generate_3regular_graph(n, seed=0)
    H = build_cost_hamiltonian(G)
    n_edges = G.number_of_edges()
    assert len(H) == n_edges + 1

    labels = [str(p) for p in H.paulis]
    coeffs = [c.real for c in H.coeffs]

    identity_label = "I" * n
    assert identity_label in labels
    assert np.isclose(coeffs[labels.index(identity_label)], -0.5 * n_edges)


# ---------------------------------------------------------------------------
# classical_cut_value validation
# ---------------------------------------------------------------------------

def test_classical_cut_k3_all_states():
    """K3 cut values: |000>=0, |111>=0, rest all = 2."""
    G = generate_triangle()
    expected = {
        "000": 0,
        "001": 2, "010": 2, "100": 2,
        "011": 2, "101": 2, "110": 2,
        "111": 0,
    }
    for bs, want in expected.items():
        assert classical_cut_value(bs, G) == want, f"C({bs}) wrong"


def test_classical_cut_length_mismatch_raises():
    G = generate_triangle()
    with pytest.raises(ValueError, match="length"):
        classical_cut_value("00", G)


def test_classical_cut_bad_characters_raises():
    G = generate_triangle()
    with pytest.raises(ValueError, match="must contain only"):
        classical_cut_value("0X1", G)
