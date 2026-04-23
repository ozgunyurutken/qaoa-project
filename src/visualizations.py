"""
Module 7 — presentation figures and data artifacts.

Generates the full set of 10 presentation figures listed in brief Section 7
plus the supporting data artifacts (`k3_detailed.json`, `aggregated_results.csv`).

Figures are saved as PNG (dpi=300) and SVG in ``results/figures/``.

Public API
----------
    setup_style()                           — apply global matplotlib style.
    save_fig(fig, stem, outdir)             — save both PNG+SVG.
    collect_k3_detailed()                   — run K₃ p=1 end-to-end, gather
                                              everything the K₃ figures need.
    make_figure_01 … make_figure_10(...)    — build a single figure, return
                                              the `Figure` object.
    generate_all(outdir="results/figures")  — produce every figure + data
                                              artifacts; returns a dict of
                                              paths for verification.

All figure functions are pure — they read from their arguments only (no
global disk I/O) — so the notebooks can call them cell-by-cell with full
control over titles and output paths.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
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
from src.optimizer import _energy, _make_tracked_objective, grid_search_p1
from scipy.optimize import minimize


# ---------------------------------------------------------------------------
# Style guide (brief §7)
# ---------------------------------------------------------------------------

COLORS = {1: "#2E86AB", 2: "#A23B72", 3: "#F18F01"}  # p=1,2,3
FARHI_BOUND = 0.6924
DEFAULT_FIG_DIR = Path("results/figures")
DEFAULT_DATA_DIR = Path("results/data")


def setup_style() -> None:
    """Apply brief §7 style: serif font, ≥12pt, clean grid."""
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 12,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "legend.fontsize": 11,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "figure.dpi": 100,
    })


def save_fig(fig: Figure, stem: str, outdir: str | Path = DEFAULT_FIG_DIR) -> dict:
    """Save both PNG (dpi=300) and SVG with the given stem. Returns paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f"{stem}.png"
    svg = outdir / f"{stem}.svg"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    return {"png": png, "svg": svg}


# ---------------------------------------------------------------------------
# K₃ detailed run — data used by figures 01, 02, 03, 04, 10
# ---------------------------------------------------------------------------

@dataclass
class K3Detailed:
    """All the pieces figures 01–04 and 10 need from one K₃ p=1 run."""
    G: nx.Graph
    n: int
    c_star: int
    gamma_opt: float
    beta_opt: float
    final_expectation: float
    approx_ratio: float
    convergence: list[float]                # warm-start COBYLA trace
    cold_convergence: list[float]           # cold-start COBYLA trace (figure 03)
    cold_start: tuple[float, float]         # (γ₀, β₀) used for cold run
    grid_size: int
    landscape_gammas: np.ndarray            # 1D axis
    landscape_betas: np.ndarray             # 1D axis
    landscape_F: np.ndarray                 # 2D (gamma, beta) -> F = <H_C>
    histogram_uniform: dict[str, float]     # before QAOA
    histogram_optimized: dict[str, float]   # after QAOA

    def to_json_dict(self) -> dict:
        return {
            "n": self.n,
            "c_star": self.c_star,
            "gamma_opt": self.gamma_opt,
            "beta_opt": self.beta_opt,
            "final_expectation": self.final_expectation,
            "approximation_ratio": self.approx_ratio,
            "convergence_history": list(self.convergence),
            "cold_convergence_history": list(self.cold_convergence),
            "cold_start": list(self.cold_start),
            "grid_size": self.grid_size,
            "landscape_gammas": self.landscape_gammas.tolist(),
            "landscape_betas": self.landscape_betas.tolist(),
            "landscape_F": self.landscape_F.tolist(),
            "histogram_uniform": self.histogram_uniform,
            "histogram_optimized": self.histogram_optimized,
        }


def collect_k3_detailed(
    grid_size: int = 50,
    shots: int = 20_000,
    cold_start: tuple[float, float] = (0.20, 0.20),
    cold_rhobeg: float = 0.15,
) -> K3Detailed:
    """Run K₃ p=1 end-to-end and collect everything the K₃ figures need.

    Produces two COBYLA traces:

    * ``convergence`` — warm-start from the grid-search optimum (mirrors the
      production ``optimize_qaoa`` pipeline, used in every other module).
    * ``cold_convergence`` — cold-start from ``cold_start`` with a small
      ``rhobeg``; for K₃ the grid already lands at the global optimum, so the
      warm run looks pedagogically flat. The cold run starts from a
      deliberately suboptimal point and walks in, giving Figure 03 a real
      descent curve.
    """
    G = generate_triangle()
    n = G.number_of_nodes()
    c_star = optimal_cut_value(G)
    H = build_cost_hamiltonian(G)

    # 1) Production path: p=1 grid → COBYLA (warm start).
    gamma0, beta0, _ = grid_search_p1(G, grid_size=grid_size)
    convergence: list[float] = []
    obj = _make_tracked_objective(G, H, p=1, history=convergence)
    res = minimize(obj, np.array([gamma0, beta0], dtype=float),
                   method="COBYLA", tol=1e-8, options={"maxiter": 200})
    gamma_opt, beta_opt = float(res.x[0]), float(res.x[1])
    final_exp = float(res.fun)
    r = approximation_ratio(final_exp, c_star)

    # 2) Pedagogical path: cold COBYLA trace for Figure 03.
    cold_history: list[float] = []
    cold_obj = _make_tracked_objective(G, H, p=1, history=cold_history)
    minimize(cold_obj, np.array(cold_start, dtype=float),
             method="COBYLA", tol=1e-8,
             options={"maxiter": 200, "rhobeg": cold_rhobeg})

    # 3) Parameter landscape over the same p=1 grid (real part of F).
    gammas_axis = np.linspace(0.0, np.pi, grid_size, endpoint=False)
    betas_axis = np.linspace(0.0, np.pi / 2, grid_size, endpoint=False)
    F = np.empty((grid_size, grid_size), dtype=float)
    for i, g in enumerate(gammas_axis):
        for j, b in enumerate(betas_axis):
            F[i, j] = _energy(G, H, p=1, gammas=[g], betas=[b])

    # 4) Before/after measurement histograms.
    qc_uniform = QuantumCircuit(n)  # H^⊗n only — no cost/mixer layers
    qc_uniform.h(range(n))
    qc_opt = qaoa_circuit(G, p=1, gammas=[gamma_opt], betas=[beta_opt])
    hist_uniform = measurement_histogram(qc_uniform, n_shots=shots)
    hist_optimized = measurement_histogram(qc_opt, n_shots=shots)

    return K3Detailed(
        G=G, n=n, c_star=c_star,
        gamma_opt=gamma_opt, beta_opt=beta_opt,
        final_expectation=final_exp, approx_ratio=r,
        convergence=list(convergence),
        cold_convergence=list(cold_history),
        cold_start=tuple(cold_start),
        grid_size=grid_size,
        landscape_gammas=gammas_axis, landscape_betas=betas_axis,
        landscape_F=F,
        histogram_uniform=hist_uniform,
        histogram_optimized=hist_optimized,
    )


# ---------------------------------------------------------------------------
# Figure 01 — K₃ QAOA circuit diagram
# ---------------------------------------------------------------------------

def make_figure_01(k3: K3Detailed) -> Figure:
    """QAOA circuit for K₃ at optimal (γ*, β*), drawn via qc.draw('mpl')."""
    qc = qaoa_circuit(k3.G, p=1, gammas=[k3.gamma_opt], betas=[k3.beta_opt])
    fig = qc.draw(output="mpl", style="iqp", fold=-1)
    fig.suptitle(
        f"K₃ QAOA circuit (p=1,  γ*={k3.gamma_opt:.3f},  β*={k3.beta_opt:.3f})",
        fontsize=13, y=1.02,
    )
    fig.set_size_inches(12, 4)
    return fig


# ---------------------------------------------------------------------------
# Figure 02 — K₃ measurement histogram after optimization
# ---------------------------------------------------------------------------

_K3_BITSTRINGS = [f"{i:03b}" for i in range(8)]
_K3_OPTIMAL = {"001", "010", "011", "100", "101", "110"}


def _ordered_probs(hist: dict[str, float], order: Iterable[str]) -> list[float]:
    return [hist.get(b, 0.0) for b in order]


def make_figure_02(k3: K3Detailed) -> Figure:
    """Bar chart of p(bitstring) after QAOA on K₃. Optimal cuts highlighted."""
    fig, ax = plt.subplots(figsize=(10, 6))
    probs = _ordered_probs(k3.histogram_optimized, _K3_BITSTRINGS)
    colors = ["#2E86AB" if b in _K3_OPTIMAL else "#888888" for b in _K3_BITSTRINGS]
    bars = ax.bar(_K3_BITSTRINGS, probs, color=colors, edgecolor="black", linewidth=0.8)
    for bar, p in zip(bars, probs):
        ax.text(bar.get_x() + bar.get_width() / 2, p + 0.005, f"{p:.3f}",
                ha="center", va="bottom", fontsize=10)
    ax.axhline(1 / 6, color="red", linestyle="--", linewidth=1,
               label="uniform over 6 optimal cuts (1/6)")
    ax.set_xlabel("bitstring |z⟩")
    ax.set_ylabel("probability")
    ax.set_title(f"K₃ QAOA output distribution  (p=1, r={k3.approx_ratio:.4f})")
    ax.set_ylim(0, max(probs) * 1.15)
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 03 — K₃ optimization curve
# ---------------------------------------------------------------------------

def make_figure_03(k3: K3Detailed) -> Figure:
    """Cost (⟨H_C⟩) vs COBYLA iteration for K₃, p=1, from a *cold* start.

    The production pipeline seeds COBYLA from the grid-search optimum, so
    its trace looks flat — the optimum is already found at iteration 1.
    For pedagogical clarity this figure uses ``k3.cold_convergence``: a
    COBYLA run starting from ``k3.cold_start`` with a small ``rhobeg`` so
    the descent toward ⟨H_C⟩ = −C* is visible.
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    raw = np.asarray(k3.cold_convergence, dtype=float)
    iters = np.arange(1, len(raw) + 1)
    best = np.minimum.accumulate(raw)

    g0, b0 = k3.cold_start
    ax.plot(iters, raw, color="0.55", linewidth=1.2, marker="o",
            markersize=4, alpha=0.9, label="raw COBYLA probes")
    ax.plot(iters, best, color=COLORS[1], linewidth=2.4,
            label="best-so-far ⟨H_C⟩")
    ax.axhline(-k3.c_star, color="red", linestyle="--", linewidth=1,
               label=f"optimum −C* = −{k3.c_star}")
    ax.set_xlabel("COBYLA iteration")
    ax.set_ylabel("expectation ⟨H_C⟩")
    ax.set_title(
        f"K₃ optimization curve  (p=1, cold start γ₀={g0:.2f}, β₀={b0:.2f};"
        f" final r={k3.approx_ratio:.4f})"
    )
    ax.legend(loc="best")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 04 — K₃ parameter landscape F(γ, β)
# ---------------------------------------------------------------------------

def make_figure_04(k3: K3Detailed) -> Figure:
    """2D heatmap of F(γ, β) = ⟨H_C⟩ over p=1 grid, with optimum marked."""
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(
        k3.landscape_F.T,   # transpose so γ is x, β is y
        extent=(k3.landscape_gammas[0], k3.landscape_gammas[-1],
                k3.landscape_betas[0], k3.landscape_betas[-1]),
        origin="lower", aspect="auto", cmap="viridis",
    )
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("⟨H_C⟩")
    ax.plot(k3.gamma_opt, k3.beta_opt, marker="*", color="red",
            markersize=18, markeredgecolor="white", linewidth=0,
            label=f"optimum (γ*={k3.gamma_opt:.3f}, β*={k3.beta_opt:.3f})")
    ax.set_xlabel("γ")
    ax.set_ylabel("β")
    ax.set_title("K₃ parameter landscape  F(γ, β) = ⟨H_C⟩  (p=1)")
    ax.legend(loc="upper right")
    ax.grid(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 05 — approximation ratio vs N (error bars per p)
# ---------------------------------------------------------------------------

def _line_per_p(ax, agg: pd.DataFrame, ycol: str, errcol: str | None = None,
                label_prefix: str = "p") -> None:
    for p in sorted(agg["p"].unique()):
        sub = agg[agg["p"] == p].sort_values("n")
        color = COLORS.get(int(p), None)
        if errcol is not None:
            ax.errorbar(sub["n"], sub[ycol], yerr=sub[errcol],
                        marker="o", capsize=4, linewidth=2, color=color,
                        label=f"{label_prefix}={p}")
        else:
            ax.plot(sub["n"], sub[ycol], marker="o", linewidth=2,
                    color=color, label=f"{label_prefix}={p}")


def make_figure_05(agg: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    _line_per_p(ax, agg, "r_mean", errcol="r_std")
    ax.axhline(FARHI_BOUND, color="red", linestyle="--", linewidth=1,
               label=f"Farhi 2014 bound ({FARHI_BOUND})")
    ax.set_xlabel("graph size N")
    ax.set_ylabel("approximation ratio r")
    ax.set_title("Approximation ratio vs N  (mean ± std across 5 seeds)")
    ax.set_ylim(0.6, 1.05)
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 06 — gate count vs N (total + CNOT, three p lines each)
# ---------------------------------------------------------------------------

def make_figure_06(agg: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    for p in sorted(agg["p"].unique()):
        sub = agg[agg["p"] == p].sort_values("n")
        color = COLORS[int(p)]
        ax.plot(sub["n"], sub["gate_mean"], marker="o", linewidth=2,
                color=color, label=f"total  (p={p})")
        ax.plot(sub["n"], sub["cnot_mean"], marker="s", linewidth=2,
                color=color, linestyle="--", label=f"CNOT  (p={p})")
    ax.set_xlabel("graph size N")
    ax.set_ylabel("gate count")
    ax.set_title("Gate count vs N  (total  vs  CNOT,  per p)")
    ax.legend(ncol=2)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 07 — circuit depth vs N (three p lines)
# ---------------------------------------------------------------------------

def make_figure_07(agg: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    _line_per_p(ax, agg, "depth_mean")
    ax.set_xlabel("graph size N")
    ax.set_ylabel("circuit depth (after transpile)")
    ax.set_title("Circuit depth vs N  (per p)")
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 08 — approximation ratio vs p (selected N)
# ---------------------------------------------------------------------------

def make_figure_08(agg: pd.DataFrame, ns: Iterable[int] = (3, 6, 8, 10)) -> Figure:
    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = plt.cm.viridis
    ns = list(ns)
    for idx, n in enumerate(ns):
        sub = agg[agg["n"] == n].sort_values("p")
        color = cmap(0.15 + 0.7 * idx / max(1, len(ns) - 1))
        ax.errorbar(sub["p"], sub["r_mean"], yerr=sub["r_std"], marker="o",
                    capsize=4, linewidth=2, color=color, label=f"N={n}")
    ax.axhline(FARHI_BOUND, color="red", linestyle="--", linewidth=1,
               label=f"Farhi 2014 bound ({FARHI_BOUND})")
    ax.set_xlabel("QAOA depth p")
    ax.set_ylabel("approximation ratio r")
    ax.set_title("Approximation ratio vs p  (mean ± std)")
    ax.set_xticks(sorted(agg["p"].unique()))
    ax.set_ylim(0.6, 1.05)
    ax.legend()
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 09 — graph examples (K₃ + 3-regular N=6)
# ---------------------------------------------------------------------------

def make_figure_09(n_3reg: int = 6, seed_3reg: int = 0) -> Figure:
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    for ax in axes:
        ax.grid(False)
        ax.set_aspect("equal")
        ax.axis("off")

    G3 = generate_triangle()
    pos3 = nx.circular_layout(G3)
    nx.draw_networkx_nodes(G3, pos3, ax=axes[0], node_size=900,
                           node_color="#A23B72", edgecolors="black")
    nx.draw_networkx_edges(G3, pos3, ax=axes[0], width=2)
    nx.draw_networkx_labels(G3, pos3, ax=axes[0], font_size=14,
                            font_color="white")
    axes[0].set_title(f"K₃  (|E|={G3.number_of_edges()})", fontsize=14)

    G_r = generate_3regular_graph(n_3reg, seed=seed_3reg)
    pos_r = nx.circular_layout(G_r)
    nx.draw_networkx_nodes(G_r, pos_r, ax=axes[1], node_size=900,
                           node_color="#2E86AB", edgecolors="black")
    nx.draw_networkx_edges(G_r, pos_r, ax=axes[1], width=2)
    nx.draw_networkx_labels(G_r, pos_r, ax=axes[1], font_size=14,
                            font_color="white")
    axes[1].set_title(
        f"random 3-regular  (N={n_3reg}, seed={seed_3reg}, |E|={G_r.number_of_edges()})",
        fontsize=14,
    )

    fig.suptitle("Graph examples used in the scaling study", fontsize=14, y=1.00)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 10 — uniform vs optimized histograms, side-by-side
# ---------------------------------------------------------------------------

def make_figure_10(k3: K3Detailed) -> Figure:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    uni = _ordered_probs(k3.histogram_uniform, _K3_BITSTRINGS)
    opt = _ordered_probs(k3.histogram_optimized, _K3_BITSTRINGS)

    for ax, probs, title, color_fn in [
        (axes[0], uni, "before QAOA (uniform superposition)",
         lambda _b: "#888888"),
        (axes[1], opt, f"after QAOA  (p=1, r={k3.approx_ratio:.4f})",
         lambda b: "#2E86AB" if b in _K3_OPTIMAL else "#888888"),
    ]:
        colors = [color_fn(b) for b in _K3_BITSTRINGS]
        ax.bar(_K3_BITSTRINGS, probs, color=colors, edgecolor="black", linewidth=0.8)
        ax.set_xlabel("bitstring |z⟩")
        ax.set_title(title)
        ax.set_ylim(0, max(max(uni), max(opt)) * 1.15)
    axes[0].set_ylabel("probability")

    # Shade optimal bitstrings on both axes for easy comparison.
    for ax in axes:
        for i, b in enumerate(_K3_BITSTRINGS):
            if b in _K3_OPTIMAL:
                ax.axvspan(i - 0.45, i + 0.45, color="#2E86AB", alpha=0.08)

    fig.suptitle("K₃ measurement histogram — before vs after QAOA", fontsize=14)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# End-to-end: data artifacts + every figure
# ---------------------------------------------------------------------------

def _ensure_aggregated_csv(df: pd.DataFrame, out: Path | None = None) -> Path:
    # Resolve at call time so tests can monkeypatch DEFAULT_DATA_DIR.
    from src.run_experiment import aggregate_results
    if out is None:
        out = DEFAULT_DATA_DIR / "aggregated_results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    agg = aggregate_results(df)
    agg.to_csv(out, index=False)
    return out


def _save_k3_detailed(k3: K3Detailed, out: Path | None = None) -> Path:
    if out is None:
        out = DEFAULT_DATA_DIR / "k3_detailed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(k3.to_json_dict(), indent=2))
    return out


def generate_all(
    outdir: str | Path | None = None,
    scaling_json: str | Path | None = None,
    verbose: bool = True,
) -> dict[str, dict[str, Path]]:
    """
    Generate every artifact:

    * 10 figures (PNG+SVG) under ``outdir``,
    * ``results/data/k3_detailed.json``,
    * ``results/data/aggregated_results.csv``.

    Returns
    -------
    dict — per-figure path mapping + ``"k3_json"`` + ``"aggregated_csv"``.
    """
    setup_style()
    # Resolve at call time so tests can monkeypatch DEFAULT_FIG_DIR / DEFAULT_DATA_DIR.
    outdir = Path(outdir) if outdir is not None else DEFAULT_FIG_DIR
    scaling_json = (Path(scaling_json) if scaling_json is not None
                    else DEFAULT_DATA_DIR / "scaling_results.json")
    if not scaling_json.exists():
        raise FileNotFoundError(
            f"{scaling_json} not found — run `python -m src.run_experiment` first."
        )

    df = pd.read_json(scaling_json, orient="records")
    from src.run_experiment import aggregate_results
    agg = aggregate_results(df)

    if verbose:
        print(f"Loaded scaling data: {len(df)} experiments, "
              f"{df['seed'].nunique()} seeds.")
        print("Running K₃ detailed demo ...")
    k3 = collect_k3_detailed()

    results: dict[str, dict[str, Path]] = {}

    if verbose:
        print("Writing figures ...")

    # 01..04 + 10 need K₃
    results["01_k3_circuit_diagram"] = save_fig(make_figure_01(k3),
                                                "01_k3_circuit_diagram", outdir)
    results["02_k3_measurement_histogram"] = save_fig(make_figure_02(k3),
                                                      "02_k3_measurement_histogram", outdir)
    results["03_k3_optimization_curve"] = save_fig(make_figure_03(k3),
                                                   "03_k3_optimization_curve", outdir)
    results["04_k3_parameter_landscape"] = save_fig(make_figure_04(k3),
                                                    "04_k3_parameter_landscape", outdir)
    # 05..08 use aggregated scaling data.
    results["05_approximation_ratio_vs_n"] = save_fig(make_figure_05(agg),
                                                      "05_approximation_ratio_vs_n", outdir)
    results["06_gate_count_vs_n"] = save_fig(make_figure_06(agg),
                                             "06_gate_count_vs_n", outdir)
    results["07_depth_vs_n"] = save_fig(make_figure_07(agg),
                                        "07_depth_vs_n", outdir)
    results["08_approximation_ratio_vs_p"] = save_fig(make_figure_08(agg),
                                                      "08_approximation_ratio_vs_p", outdir)
    # 09 + 10
    results["09_graph_examples"] = save_fig(make_figure_09(),
                                            "09_graph_examples", outdir)
    results["10_histogram_comparison"] = save_fig(make_figure_10(k3),
                                                  "10_histogram_comparison", outdir)

    # Data artifacts
    k3_path = _save_k3_detailed(k3)
    agg_path = _ensure_aggregated_csv(df)
    results["k3_json"] = {"json": k3_path}
    results["aggregated_csv"] = {"csv": agg_path}

    # Close figures we opened so CLI runs don't leak memory.
    plt.close("all")

    if verbose:
        print(f"\nWrote {len([k for k in results if k.startswith('0') or k.startswith('10')])}"
              f" figures to {outdir}")
        print(f"  k3_detailed.json -> {k3_path}")
        print(f"  aggregated_results.csv -> {agg_path}")

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate all 10 presentation figures.")
    parser.add_argument("--outdir", default=str(DEFAULT_FIG_DIR), type=str)
    parser.add_argument("--scaling-json",
                        default=str(DEFAULT_DATA_DIR / "scaling_results.json"),
                        type=str)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    paths = generate_all(outdir=args.outdir, scaling_json=args.scaling_json,
                         verbose=not args.quiet)

    print("\nGenerated artifacts:")
    for stem, fmt_map in paths.items():
        for fmt, p in fmt_map.items():
            print(f"  [{fmt}] {p}")
