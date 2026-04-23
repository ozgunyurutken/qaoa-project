"""
Module 3 — QAOA ansatz circuit builder.

The ansatz implements the standard Farhi QAOA form (Option 1 convention):

    |ψ_p(γ, β)⟩ = U_B(β_p) U_C(γ_p) ... U_B(β_1) U_C(γ_1)  H⊗n |0⟩⊗n

where

    U_C(γ) = ∏_{(i,j)∈E} exp(-i γ/2 · Z_i Z_j)     (identity term in H_C is a global phase, dropped)
    U_B(β) = ∏_i  R_x(2β)                           (since R_x(θ) = exp(-i θ/2 · X))

Each edge's two-qubit rotation is decomposed as

    CNOT(i,j) —  R_z(γ, j)  — CNOT(i,j)

yielding exactly 2·|E| CNOTs per p-layer — matches the brief's gate-count
ground truths (K3 p=1 → 6 CNOTs, K3 p=2 → 12 CNOTs).

Public API:
    cost_layer(qc, G, gamma)
    mixer_layer(qc, n, beta)
    qaoa_circuit(G, p, gammas, betas)          # concrete numerical parameters
    qaoa_circuit_parametric(G, p)              # Qiskit Parameters (for optimizer)
    transpile_circuit(qc, optimization_level=2)
"""
from __future__ import annotations

from typing import Sequence

import networkx as nx
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter


def _node_to_qubit_map(G: nx.Graph) -> dict:
    """Canonical node -> qubit index map (sorted node order)."""
    return {node: idx for idx, node in enumerate(sorted(G.nodes()))}


def cost_layer(qc: QuantumCircuit, G: nx.Graph, gamma) -> None:
    """
    Apply one cost-Hamiltonian layer U_C(γ) to `qc` in place.

    Decomposition per edge:  CX(i,j) — Rz(γ, j) — CX(i,j)
    (equivalent to R_zz(γ) up to gate count; matches the brief's expected
    CNOT count of 2·|E| per p-layer).
    """
    node_to_q = _node_to_qubit_map(G)
    for u, v in G.edges():
        i = node_to_q[u]
        j = node_to_q[v]
        qc.cx(i, j)
        qc.rz(gamma, j)
        qc.cx(i, j)


def mixer_layer(qc: QuantumCircuit, n: int, beta) -> None:
    """
    Apply one mixer-Hamiltonian layer U_B(β) = ∏_i R_x(2β) in place.
    """
    for i in range(n):
        qc.rx(2.0 * beta, i)


def _build_ansatz(G: nx.Graph, p: int, gammas, betas) -> QuantumCircuit:
    """Shared builder used by both concrete and parametric wrappers."""
    if p < 1:
        raise ValueError(f"p must be >= 1, got {p}")
    if len(gammas) != p or len(betas) != p:
        raise ValueError(
            f"Expected p={p} gammas and p={p} betas, "
            f"got {len(gammas)} gammas and {len(betas)} betas"
        )

    n = G.number_of_nodes()
    qc = QuantumCircuit(n, name=f"QAOA_p{p}")
    # 1) Initial uniform superposition
    qc.h(range(n))
    # 2) p alternating layers
    for k in range(p):
        cost_layer(qc, G, gammas[k])
        mixer_layer(qc, n, betas[k])
    return qc


def qaoa_circuit(
    G: nx.Graph,
    p: int,
    gammas: Sequence[float],
    betas: Sequence[float],
) -> QuantumCircuit:
    """QAOA ansatz with concrete numerical parameters."""
    return _build_ansatz(G, p, list(gammas), list(betas))


def qaoa_circuit_parametric(
    G: nx.Graph, p: int
) -> tuple[QuantumCircuit, list[Parameter], list[Parameter]]:
    """
    QAOA ansatz as a Qiskit parametric circuit with 2p Parameters.

    Returns
    -------
    (circuit, gammas, betas)
        `gammas` and `betas` are lists of `qiskit.circuit.Parameter`
        objects of length p each; bind with `circuit.assign_parameters({...})`.
    """
    if p < 1:
        raise ValueError(f"p must be >= 1, got {p}")
    gammas = [Parameter(f"gamma_{k+1}") for k in range(p)]
    betas = [Parameter(f"beta_{k+1}") for k in range(p)]
    qc = _build_ansatz(G, p, gammas, betas)
    return qc, gammas, betas


def transpile_circuit(
    qc: QuantumCircuit, optimization_level: int = 2
) -> QuantumCircuit:
    """
    Transpile to a fixed basis {cx, rz, rx, h}. Using an explicit basis
    makes gate counts reproducible across Qiskit versions.
    """
    return transpile(
        qc,
        basis_gates=["cx", "rz", "rx", "h"],
        optimization_level=optimization_level,
    )


if __name__ == "__main__":
    # Demo:  python -m src.circuit
    import numpy as np

    from src.graph_generator import generate_3regular_graph, generate_triangle
    from src.hamiltonian import build_cost_hamiltonian

    print("=" * 60)
    print("Module 3 demo — circuit")
    print("=" * 60)

    K3 = generate_triangle()

    print("\n[1] K3 QAOA circuit at p=1 (γ=0.3, β=0.2):")
    qc1 = qaoa_circuit(K3, p=1, gammas=[0.3], betas=[0.2])
    print(f"    gates = {dict(qc1.count_ops())}")
    print(f"    num_qubits = {qc1.num_qubits}, depth = {qc1.depth()}")
    print(f"    CNOTs      = {qc1.count_ops().get('cx', 0)}  (expected 2*|E|*p = 6)")

    print("\n[2] K3 QAOA circuit at p=2:")
    qc2 = qaoa_circuit(K3, p=2, gammas=[0.3, 0.5], betas=[0.2, 0.4])
    print(f"    gates = {dict(qc2.count_ops())}")
    print(f"    depth = {qc2.depth()}")
    print(f"    CNOTs = {qc2.count_ops().get('cx', 0)}  (expected 12)")

    print("\n[3] Parametric circuit (2p Parameters):")
    for p in (1, 2, 3):
        qcp, _, _ = qaoa_circuit_parametric(K3, p=p)
        print(f"    p={p}: num_parameters = {qcp.num_parameters}")

    print("\n[4] CNOT and depth vs p (3-regular n=6, seed=0):")
    G6 = generate_3regular_graph(6, seed=0)
    print(f"    {'p':>3}  {'CNOTs':>6}  {'depth':>6}  (|E|={G6.number_of_edges()})")
    for p in range(1, 4):
        qc = qaoa_circuit(G6, p=p, gammas=[0.1] * p, betas=[0.2] * p)
        print(f"    {p:>3}  {qc.count_ops().get('cx', 0):>6}  {qc.depth():>6}")

    print("\n[5] Zero parameters -> uniform superposition (sanity):")
    from qiskit.quantum_info import Statevector
    qc0 = qaoa_circuit(K3, p=1, gammas=[0.0], betas=[0.0])
    sv = Statevector(qc0)
    probs = np.abs(sv.data) ** 2
    print(f"    probabilities = {np.round(probs, 6).tolist()}")
    print(f"    all equal to 1/8 = 0.125? -> {np.allclose(probs, 1/8)}")

    print("\n[6] Transpile (optimization_level=2) preserves expectation:")
    H = build_cost_hamiltonian(K3)
    ev_raw = Statevector(qc2).expectation_value(H).real
    qc2t = transpile_circuit(qc2, optimization_level=2)
    ev_trans = Statevector(qc2t).expectation_value(H).real
    print(f"    <H_C> raw        = {ev_raw:+.8f}")
    print(f"    <H_C> transpiled = {ev_trans:+.8f}")
    print(f"    match? {np.isclose(ev_raw, ev_trans)}")
