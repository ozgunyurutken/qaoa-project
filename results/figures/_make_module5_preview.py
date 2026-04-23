"""Module 5 sanity preview — 2×2 grid.

    (a) K₃ p=1  r(γ, β) landscape with optimiser trajectory overlaid.
    (b) Convergence curve (best-so-far) for K₃, p ∈ {1, 2, 3}.
    (c) r vs N for p=1 with Farhi 2014 bound.
    (d) Warm-start vs cold random init on n=6, p=2.

Saved to results/figures/module5_optimizer_preview.png at dpi=200.
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import minimize

from src.circuit import qaoa_circuit
from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value
from src.metrics import approximation_ratio, expectation_value
from src.optimizer import grid_search_p1, optimize_qaoa


def panel_a_landscape_with_trajectory(ax) -> None:
    """Landscape r(γ, β) for K₃, p=1 with COBYLA path overlaid."""
    K3 = generate_triangle()
    H = build_cost_hamiltonian(K3)
    C_star = optimal_cut_value(K3)

    n_g, n_b = 81, 41
    gammas = np.linspace(0, np.pi, n_g)
    betas = np.linspace(0, np.pi / 2, n_b)
    R = np.zeros((n_b, n_g))
    for i, b in enumerate(betas):
        for j, g in enumerate(gammas):
            ev = float(expectation_value(qaoa_circuit(K3, p=1, gammas=[g], betas=[b]), H))
            R[i, j] = approximation_ratio(ev, C_star)

    im = ax.imshow(R, origin="lower", aspect="auto", cmap="viridis",
                   extent=[gammas[0], gammas[-1], betas[0], betas[-1]],
                   vmin=0, vmax=1)

    # Overlay COBYLA trajectory starting from the grid-search best point.
    g0, b0, _ = grid_search_p1(K3, grid_size=20)
    traj_g = [g0]
    traj_b = [b0]

    def obj(x):
        ev = float(expectation_value(qaoa_circuit(K3, p=1, gammas=[x[0]], betas=[x[1]]), H))
        traj_g.append(x[0])
        traj_b.append(x[1])
        return ev

    minimize(obj, np.array([g0, b0]), method="COBYLA", tol=1e-8, options={"maxiter": 200})
    ax.plot(traj_g, traj_b, "r.-", markersize=3, linewidth=0.8, alpha=0.9,
            label="COBYLA path")
    ax.plot([traj_g[0]], [traj_b[0]], "wo", markersize=8, markeredgecolor="black",
            label="grid seed")
    ax.plot([traj_g[-1]], [traj_b[-1]], "w*", markersize=12, markeredgecolor="black",
            label="optimum")
    ax.set_xlabel("γ"); ax.set_ylabel("β")
    ax.set_title(f"(a) K₃ p=1 r(γ, β) with COBYLA path   r*={R.max():.3f}", fontsize=10)
    ax.legend(fontsize=8, loc="upper right")
    plt.colorbar(im, ax=ax, label="r")


def panel_b_convergence_curves(ax) -> None:
    """Best-so-far cost vs COBYLA function evaluation for K₃ at p=1..3."""
    K3 = generate_triangle()
    for p, color in zip([1, 2, 3], ["tab:blue", "tab:orange", "tab:green"]):
        res = optimize_qaoa(K3, p=p, p1_grid_size=20, layer_grid_size=5)
        hist = np.array(res["convergence_history"])
        best = np.minimum.accumulate(hist)
        ax.plot(range(1, len(best) + 1), best, color=color,
                label=f"p={p}, final r={res['approximation_ratio']:.3f}")
    ax.axhline(-optimal_cut_value(K3), color="red", linestyle="--", linewidth=1,
               label=f"-C* = {-optimal_cut_value(K3)}")
    ax.set_xlabel("COBYLA evaluation #"); ax.set_ylabel("best-so-far ⟨H_C⟩")
    ax.set_title("(b) K₃ convergence curves", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")


def panel_c_r_vs_n(ax) -> None:
    """r vs N at p=1 with Farhi bound reference."""
    ns = [3, 4, 6, 8, 10]
    rs = []
    for n in ns:
        G = generate_triangle() if n == 3 else generate_3regular_graph(n, seed=0)
        res = optimize_qaoa(G, p=1, p1_grid_size=30)
        rs.append(res["approximation_ratio"])
    ax.plot(ns, rs, "o-", color="tab:purple", label="p=1 optimum (seed=0)")
    ax.axhline(0.6924, color="red", linestyle="--", linewidth=1,
               label="Farhi bound 0.6924")
    for n, r in zip(ns, rs):
        ax.text(n, r + 0.015, f"{r:.3f}", ha="center", fontsize=8)
    ax.set_xlabel("N"); ax.set_ylabel("r")
    ax.set_ylim(0.6, 1.05)
    ax.set_title("(c) p=1 optimum vs N  (K₃ + 3-regular seed=0)", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower left")


def panel_d_warm_vs_cold(ax) -> None:
    """n=6, p=2: warm-start convergence curve vs 3 cold-start trajectories."""
    G = generate_3regular_graph(6, seed=0)
    H = build_cost_hamiltonian(G)
    C_star = optimal_cut_value(G)

    # Warm start from layer-by-layer
    warm = optimize_qaoa(G, p=2)
    warm_best = np.minimum.accumulate(warm["convergence_history"])
    # r curve: convert ⟨H_C⟩ to r
    warm_r = -warm_best / C_star

    rng = np.random.default_rng(0)
    cold_curves = []
    for trial in range(3):
        history = []
        x0 = np.concatenate([rng.uniform(0, np.pi, 2), rng.uniform(0, np.pi / 2, 2)])

        def obj(x):
            val = float(expectation_value(
                qaoa_circuit(G, p=2, gammas=x[:2], betas=x[2:]), H))
            history.append(val)
            return val

        minimize(obj, x0, method="COBYLA", tol=1e-6, options={"maxiter": 200})
        cold_curves.append(np.minimum.accumulate(history))

    ax.plot(range(1, len(warm_r) + 1), warm_r, color="tab:green", linewidth=2,
            label=f"warm (layer-by-layer), final r={warm_r[-1]:.3f}")
    for i, curve in enumerate(cold_curves):
        r_curve = -curve / C_star
        ax.plot(range(1, len(r_curve) + 1), r_curve, color="tab:red",
                alpha=0.4, linewidth=1, label=f"cold trial {i+1}" if i == 0 else None)
    ax.axhline(0.6924, color="red", linestyle="--", linewidth=1, alpha=0.6,
               label="Farhi 0.6924")
    ax.set_xlabel("COBYLA evaluation #"); ax.set_ylabel("best-so-far r")
    ax.set_title("(d) warm vs cold start — 3-reg n=6, p=2", fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="lower right")


def main() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    panel_a_landscape_with_trajectory(axes[0, 0])
    panel_b_convergence_curves(axes[0, 1])
    panel_c_r_vs_n(axes[1, 0])
    panel_d_warm_vs_cold(axes[1, 1])
    fig.suptitle("Module 5 — optimizer sanity", fontsize=13, y=1.00)
    fig.tight_layout()
    out = "results/figures/module5_optimizer_preview.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
