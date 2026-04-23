"""Module 4 sanity preview: four metrics in a 2×2 grid.

    (a) K₃ QAOA <H_C> and r over a grid of (γ, β) at p=1.
    (b) Approximation ratio for QAOA(p=1, γ=0.3, β=0.2) across graphs.
    (c) CNOT and total gate count vs N for p ∈ {1,2,3}  (3-regular seed=0).
    (d) Measurement histogram for |+⟩^3 vs optimised QAOA(p=1) on K₃.

Saved to results/figures/module4_metrics_preview.png at dpi=200.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from qiskit import QuantumCircuit

from src.circuit import qaoa_circuit
from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value
from src.metrics import (
    approximation_ratio,
    expectation_value,
    gate_count,
    measurement_histogram,
)


def panel_a_landscape(ax) -> None:
    """K₃, p=1: heatmap of r(γ, β) over [0, π] × [0, π/2]."""
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    C_star = optimal_cut_value(K3)

    n_gamma, n_beta = 41, 21
    gammas = np.linspace(0, np.pi, n_gamma)
    betas = np.linspace(0, np.pi / 2, n_beta)
    R = np.zeros((n_beta, n_gamma))
    for i, b in enumerate(betas):
        for j, g in enumerate(gammas):
            qc = qaoa_circuit(K3, p=1, gammas=[g], betas=[b])
            ev = expectation_value(qc, H)
            R[i, j] = approximation_ratio(ev, C_star)

    im = ax.imshow(R, origin="lower", aspect="auto", cmap="viridis",
                   extent=[gammas[0], gammas[-1], betas[0], betas[-1]],
                   vmin=0, vmax=1)
    ax.set_xlabel("γ")
    ax.set_ylabel("β")
    ax.set_title(f"(a) K₃ p=1  approximation ratio r(γ, β)   max={R.max():.3f}",
                 fontsize=10)
    plt.colorbar(im, ax=ax, label="r")


def panel_b_ratio_vs_graph(ax) -> None:
    """Bar chart of r at fixed params (γ=0.3, β=0.2) across graphs."""
    graphs = {
        "K₃": generate_triangle(),
        "n=4": generate_3regular_graph(4, seed=0),
        "n=6": generate_3regular_graph(6, seed=0),
        "n=8": generate_3regular_graph(8, seed=0),
        "n=10": generate_3regular_graph(10, seed=0),
    }
    rs = []
    labels = []
    for label, G in graphs.items():
        H = build_cost_hamiltonian(G)
        C_star = optimal_cut_value(G)
        qc = qaoa_circuit(G, p=1, gammas=[0.3], betas=[0.2])
        ev = expectation_value(qc, H)
        rs.append(approximation_ratio(ev, C_star))
        labels.append(label)
    bars = ax.bar(labels, rs, color="tab:blue", edgecolor="black")
    ax.axhline(0.6924, color="red", linestyle="--", linewidth=1,
               label="Farhi 2014 bound (0.6924)")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("r")
    ax.set_title("(b) r at fixed (γ=0.3, β=0.2), p=1  (before optimization)", fontsize=10)
    for bar, r in zip(bars, rs):
        ax.text(bar.get_x() + bar.get_width() / 2, r + 0.02, f"{r:.3f}",
                ha="center", fontsize=8)
    ax.legend(fontsize=8, loc="lower right")


def panel_c_gate_scaling(ax) -> None:
    """CNOT and total gate count vs N for p ∈ {1,2,3}."""
    ns = [3, 4, 6, 8, 10]
    for p, color in zip([1, 2, 3], ["tab:blue", "tab:orange", "tab:green"]):
        cnots, totals = [], []
        for n in ns:
            G = generate_triangle() if n == 3 else generate_3regular_graph(n, seed=0)
            qc = qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p)
            gc = gate_count(qc, transpiled=True)
            cnots.append(gc["cnot"])
            totals.append(gc["total"])
        ax.plot(ns, cnots, marker="o", color=color, label=f"p={p} CNOTs")
        ax.plot(ns, totals, marker="s", linestyle="--", color=color, alpha=0.6,
                label=f"p={p} total")
    ax.set_xlabel("N (graph size)")
    ax.set_ylabel("count")
    ax.set_title("(c) Gate count vs N", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2)


def panel_d_histograms(ax) -> None:
    """|+⟩^3 vs QAOA(p=1) histogram on K₃ — side-by-side bars."""
    K3 = generate_triangle()

    qc_plus = QuantumCircuit(3)
    qc_plus.h(range(3))
    hist_plus = measurement_histogram(qc_plus, n_shots=20_000)

    qc_qaoa = qaoa_circuit(K3, p=1, gammas=[0.3], betas=[0.2])
    hist_qaoa = measurement_histogram(qc_qaoa, n_shots=20_000)

    states = [f"{i:03b}" for i in range(8)]
    plus_vals = [hist_plus.get(s, 0) for s in states]
    qaoa_vals = [hist_qaoa.get(s, 0) for s in states]

    x = np.arange(len(states))
    width = 0.35
    ax.bar(x - width / 2, plus_vals, width, label="|+⟩⊗3 (uniform)", color="lightgray")
    ax.bar(x + width / 2, qaoa_vals, width, label="QAOA(p=1, γ=0.3, β=0.2)", color="tab:purple")
    ax.set_xticks(x)
    ax.set_xticklabels(states, rotation=45)
    ax.set_ylabel("probability")
    ax.set_title("(d) Measurement histogram on K₃", fontsize=10)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    panel_a_landscape(axes[0, 0])
    panel_b_ratio_vs_graph(axes[0, 1])
    panel_c_gate_scaling(axes[1, 0])
    panel_d_histograms(axes[1, 1])
    fig.suptitle("Module 4 — metrics sanity", fontsize=13, y=1.00)
    fig.tight_layout()
    out = "results/figures/module4_metrics_preview.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
