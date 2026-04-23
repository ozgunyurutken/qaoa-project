"""Module 3 sanity preview:
    left  — K3 QAOA p=1 circuit diagram (qc.draw('mpl'))
    right — CNOT count and depth vs p for K3 / 3-reg n=6 / 3-reg n=8

Saved to results/figures/module3_circuit_preview.png at dpi=200.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from src.circuit import qaoa_circuit
from src.graph_generator import generate_3regular_graph, generate_triangle


def main() -> None:
    fig = plt.figure(figsize=(14, 5))

    # Left: K3 p=1 circuit diagram (mpl drawer)
    ax_left = fig.add_subplot(1, 2, 1)
    qc = qaoa_circuit(generate_triangle(), p=1, gammas=[0.3], betas=[0.2])
    qc.draw(output="mpl", ax=ax_left, style="iqp")
    ax_left.set_title("K$_3$ QAOA ansatz, p=1 (γ=0.3, β=0.2) — 6 CNOTs", fontsize=11)

    # Right: CNOT + depth vs p scaling (preview extends to p=6 for visual clarity;
    # actual experiments stay at p in {1,2,3} per the brief).
    ax_right = fig.add_subplot(1, 2, 2)
    ps = list(range(1, 7))  # 1..6
    graphs = {
        "K$_3$ (|E|=3)": generate_triangle(),
        "3-reg n=6 (|E|=9)": generate_3regular_graph(6, seed=0),
        "3-reg n=8 (|E|=12)": generate_3regular_graph(8, seed=0),
    }
    markers = {"K$_3$ (|E|=3)": "o", "3-reg n=6 (|E|=9)": "s", "3-reg n=8 (|E|=12)": "^"}
    colors = {"K$_3$ (|E|=3)": "tab:blue", "3-reg n=6 (|E|=9)": "tab:orange", "3-reg n=8 (|E|=12)": "tab:green"}

    for label, G in graphs.items():
        cnots = []
        depths = []
        for p in ps:
            qc = qaoa_circuit(G, p=p, gammas=[0.1] * p, betas=[0.2] * p)
            cnots.append(qc.count_ops().get("cx", 0))
            depths.append(qc.depth())
        ax_right.plot(ps, cnots, marker=markers[label], linestyle="-",
                      color=colors[label], label=f"{label} CNOTs")
        ax_right.plot(ps, depths, marker=markers[label], linestyle="--",
                      color=colors[label], alpha=0.6, label=f"{label} depth")

    # Shade the study's actual experimental range p in {1,2,3}.
    ax_right.axvspan(1, 3, color="gray", alpha=0.08, zorder=0)
    ax_right.text(2, ax_right.get_ylim()[1] if False else 0, "",)
    ax_right.set_xlabel("p")
    ax_right.set_ylabel("count")
    ax_right.set_xticks(ps)
    ax_right.set_title("CNOT and depth scale linearly in p  (shaded: study range p∈{1,2,3})",
                       fontsize=10)
    ax_right.grid(True, alpha=0.3)
    ax_right.legend(fontsize=8, ncol=2, loc="upper left")

    fig.suptitle("Module 3 — QAOA circuit sanity", fontsize=13, y=1.02)
    fig.tight_layout()
    out = "results/figures/module3_circuit_preview.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
