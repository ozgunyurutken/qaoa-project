"""
Module 2 — MaxCut Hamiltonian (cost + mixer) in Option 1 convention.

Convention (Option 1 / minimization form):

    H_C = (1/2) * sum_{(i,j) in E} (Z_i Z_j - I)

    eigenvalues(H_C) = -C(z)

    approximation ratio   r = -<H_C> / C*

This is Qiskit-compatible. Do NOT confuse with Farhi's maximization
form which uses the opposite sign.

Mixer:

    H_B = sum_i X_i

Bit-string convention: we follow Qiskit, where the *rightmost*
character corresponds to qubit 0 (little-endian). That is, the state
|001> has qubit 0 in |1> and qubits 1, 2 in |0>.

Public API:
    build_cost_hamiltonian(G)
    build_mixer_hamiltonian(n)
    classical_cut_value(bitstring, G)
    optimal_cut_value(G)
"""
from __future__ import annotations

from itertools import product

import networkx as nx
from qiskit.quantum_info import SparsePauliOp


def _nodes_to_qubits(G: nx.Graph) -> tuple[list, dict]:
    """Canonical node -> qubit index map (sorted order)."""
    nodes = sorted(G.nodes())
    return nodes, {node: idx for idx, node in enumerate(nodes)}


def build_cost_hamiltonian(G: nx.Graph) -> SparsePauliOp:
    """
    Build MaxCut cost Hamiltonian in Option 1 (minimization) convention.

        H_C = (1/2) * sum_{(i,j) in E} (Z_i Z_j - I)

    Returns |E| ZZ terms (coefficient +1/2 each) plus a single identity
    term with coefficient -|E|/2.
    """
    nodes, node_to_qubit = _nodes_to_qubits(G)
    n = len(nodes)
    n_edges = G.number_of_edges()

    pauli_terms: list[tuple[str, float]] = []
    for u, v in G.edges():
        i = node_to_qubit[u]
        j = node_to_qubit[v]
        label = ["I"] * n
        # Qiskit label is read right-to-left: rightmost char -> qubit 0
        label[n - 1 - i] = "Z"
        label[n - 1 - j] = "Z"
        pauli_terms.append(("".join(label), 0.5))

    # Single aggregated identity term: -(|E|/2) * I
    pauli_terms.append(("I" * n, -0.5 * n_edges))

    return SparsePauliOp.from_list(pauli_terms)


def build_mixer_hamiltonian(n: int) -> SparsePauliOp:
    """
    Transverse-field mixer:  H_B = sum_i X_i   on n qubits.
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")

    pauli_terms: list[tuple[str, float]] = []
    for i in range(n):
        label = ["I"] * n
        label[n - 1 - i] = "X"
        pauli_terms.append(("".join(label), 1.0))
    return SparsePauliOp.from_list(pauli_terms)


def classical_cut_value(bitstring: str, G: nx.Graph) -> int:
    """
    Classical MaxCut value C(z) = number of edges (i, j) with z_i != z_j.

    `bitstring` uses Qiskit little-endian convention: the *rightmost*
    character is qubit 0. For example, '001' => z_0=1, z_1=0, z_2=0.
    """
    nodes, node_to_qubit = _nodes_to_qubits(G)
    n = len(nodes)

    if len(bitstring) != n:
        raise ValueError(
            f"bitstring length {len(bitstring)} does not match graph size {n}"
        )
    if any(ch not in "01" for ch in bitstring):
        raise ValueError(f"bitstring must contain only '0'/'1', got {bitstring!r}")

    # Map qubit index -> bit value (qubit 0 is rightmost char).
    def bit(qubit_idx: int) -> int:
        return int(bitstring[n - 1 - qubit_idx])

    cut = 0
    for u, v in G.edges():
        if bit(node_to_qubit[u]) != bit(node_to_qubit[v]):
            cut += 1
    return cut


def optimal_cut_value(G: nx.Graph) -> int:
    """
    True MaxCut optimum by brute-force enumeration.
    Feasible for n <= ~20 (2^20 ~ 1M states).
    """
    n = G.number_of_nodes()
    if n > 20:
        raise ValueError(
            f"optimal_cut_value is brute force; n <= 20 supported, got n={n}"
        )

    best = 0
    for bits in product("01", repeat=n):
        c = classical_cut_value("".join(bits), G)
        if c > best:
            best = c
    return best


if __name__ == "__main__":
    # Demo:  python -m src.hamiltonian
    import numpy as np

    from src.graph_generator import generate_triangle, generate_3regular_graph

    print("=" * 60)
    print("Module 2 demo — hamiltonian")
    print("=" * 60)

    print("\n[1] K3 cost Hamiltonian H_C (Option 1 convention):")
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    print(f"    number of Pauli terms : {len(H)}")
    for lbl, coeff in zip(H.paulis, H.coeffs):
        print(f"      {lbl}   coeff = {coeff.real:+.2f}")

    print("\n[2] K3 spectrum of H_C (expected: -2 x6, 0 x2):")
    eigs = np.round(np.linalg.eigvalsh(H.to_matrix()), 8)
    uniq, counts = np.unique(eigs, return_counts=True)
    for e, c in zip(uniq, counts):
        print(f"      eigenvalue {e:+.1f}   multiplicity {c}")

    print("\n[3] Classical cut C(z) on K3 for every basis state:")
    for z in range(8):
        bs = format(z, "03b")
        c = classical_cut_value(bs, K3)
        marker = "  <-- optimal" if c == 2 else ""
        print(f"      |{bs}>   C = {c}{marker}")

    print("\n[4] Optimal cut values (brute force):")
    print(f"      K3                         : C* = {optimal_cut_value(K3)}")
    import networkx as nx
    print(f"      K4 (complete, 4 nodes)     : C* = {optimal_cut_value(nx.complete_graph(4))}")
    print(f"      K5                         : C* = {optimal_cut_value(nx.complete_graph(5))}  (expected floor(25/4)=6)")
    for n in (4, 6, 8):
        G = generate_3regular_graph(n, seed=0)
        print(f"      3-regular n={n} (seed=0)    : C* = {optimal_cut_value(G)}  (|E|={G.number_of_edges()})")

    print("\n[5] Mixer H_B for n=3:")
    HB = build_mixer_hamiltonian(3)
    print(f"    terms: {len(HB)} (expected 3 = one X_i per qubit)")
    for lbl, coeff in zip(HB.paulis, HB.coeffs):
        print(f"      {lbl}   coeff = {coeff.real:+.2f}")
