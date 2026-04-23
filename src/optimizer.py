"""
Module 5 — optimizer.

Optimize the QAOA parameters (γ, β) for a given graph and depth `p`.

Strategy (brief Section 3.2):

    p = 1  → 2-D grid search on (γ, β) over [0, π) × [0, π/2), then COBYLA refine.
    p > 1  → warm-start from the p-1 solution:
              (a) fix [γ_1..γ_{p-1}, β_1..β_{p-1}]
              (b) small grid search on the new (γ_p, β_p)
              (c) COBYLA refine all 2p parameters together.

Public API:
    grid_search_p1(G, grid_size=50) -> (γ*, β*, <H_C>*)
    cobyla_refine(G, p, x0, max_iter=200, tol=1e-6) -> scipy OptimizeResult
    optimize_qaoa(G, p, max_iter=200, tol=1e-6) -> dict

Parameter layout for 2p-vector:  x = [γ_1, ..., γ_p, β_1, ..., β_p].

All energies are computed *exactly* via `Statevector` (no sampling), matching
Module 4's `expectation_value`.  We import that function so any convention
change there propagates automatically.
"""
from __future__ import annotations

import time
from typing import Sequence

import networkx as nx
import numpy as np
from scipy.optimize import OptimizeResult, minimize

from src.circuit import qaoa_circuit
from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value
from src.metrics import approximation_ratio, expectation_value


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _energy(G: nx.Graph, H, p: int, gammas: Sequence[float], betas: Sequence[float]) -> float:
    """Exact ⟨H_C⟩ for QAOA(G, p, γ, β)."""
    qc = qaoa_circuit(G, p=p, gammas=list(gammas), betas=list(betas))
    return expectation_value(qc, H)


def _make_tracked_objective(G, H, p: int, history: list[float]):
    """Closure: objective on 2p-vector that appends each evaluation to `history`."""
    def obj(x: np.ndarray) -> float:
        gammas = x[:p]
        betas = x[p:]
        val = _energy(G, H, p, gammas, betas)
        history.append(val)
        return val
    return obj


# ---------------------------------------------------------------------------
# Public: grid search at p=1
# ---------------------------------------------------------------------------

def grid_search_p1(G: nx.Graph, grid_size: int = 50) -> tuple[float, float, float]:
    """
    2-D grid search for p=1.

    γ ∈ [0, π),  β ∈ [0, π/2)  — both open at the right endpoint because the
    QAOA state is periodic and the endpoints repeat the start.
    """
    if grid_size < 2:
        raise ValueError(f"grid_size must be >= 2, got {grid_size}")

    H = build_cost_hamiltonian(G)
    gammas = np.linspace(0.0, np.pi, grid_size, endpoint=False)
    betas = np.linspace(0.0, np.pi / 2, grid_size, endpoint=False)

    best_ev = np.inf
    best_g = 0.0
    best_b = 0.0
    for g in gammas:
        for b in betas:
            ev = _energy(G, H, p=1, gammas=[g], betas=[b])
            if ev < best_ev:
                best_ev = ev
                best_g = float(g)
                best_b = float(b)
    return best_g, best_b, float(best_ev)


def _grid_search_new_layer(
    G: nx.Graph,
    p: int,
    gammas_prev: Sequence[float],
    betas_prev: Sequence[float],
    grid_size: int = 10,
) -> tuple[float, float, float]:
    """
    Small grid search over the *new* (γ_p, β_p) with the previous p-1 layers
    held fixed. Used as warm-start initialisation inside `optimize_qaoa`.
    """
    H = build_cost_hamiltonian(G)
    gammas_grid = np.linspace(0.0, np.pi, grid_size, endpoint=False)
    betas_grid = np.linspace(0.0, np.pi / 2, grid_size, endpoint=False)

    best_ev = np.inf
    best_g = 0.0
    best_b = 0.0
    for g in gammas_grid:
        for b in betas_grid:
            ev = _energy(
                G, H, p=p,
                gammas=list(gammas_prev) + [g],
                betas=list(betas_prev) + [b],
            )
            if ev < best_ev:
                best_ev = ev
                best_g = float(g)
                best_b = float(b)
    return best_g, best_b, float(best_ev)


# ---------------------------------------------------------------------------
# Public: COBYLA refinement
# ---------------------------------------------------------------------------

def cobyla_refine(
    G: nx.Graph,
    p: int,
    x0: np.ndarray,
    max_iter: int = 200,
    tol: float = 1e-6,
) -> OptimizeResult:
    """
    Thin wrapper around `scipy.optimize.minimize(method='COBYLA', ...)`.

    `x0` must have length 2p, laid out as [γ_1..γ_p, β_1..β_p].
    """
    x0 = np.asarray(x0, dtype=float)
    if x0.shape != (2 * p,):
        raise ValueError(f"x0 must have shape ({2 * p},), got {x0.shape}")

    H = build_cost_hamiltonian(G)

    def obj(x: np.ndarray) -> float:
        return _energy(G, H, p, x[:p], x[p:])

    return minimize(obj, x0, method="COBYLA", tol=tol, options={"maxiter": max_iter})


# ---------------------------------------------------------------------------
# Public: full pipeline (layer-by-layer + COBYLA)
# ---------------------------------------------------------------------------

def optimize_qaoa(
    G: nx.Graph,
    p: int,
    max_iter: int = 200,
    tol: float = 1e-6,
    p1_grid_size: int = 50,
    layer_grid_size: int = 10,
) -> dict:
    """
    Layer-by-layer QAOA optimisation.

    Returns a dict with:
        gammas, betas                  — optimised parameters (length p)
        final_expectation              — ⟨H_C⟩ at optimum
        approximation_ratio            — r = -⟨H_C⟩ / C*
        n_iterations                   — total COBYLA function evaluations
        convergence_history            — list[float] of ⟨H_C⟩ per COBYLA eval
        wall_time_seconds              — elapsed wall time
    """
    if p < 1:
        raise ValueError(f"p must be >= 1, got {p}")

    t0 = time.time()
    H = build_cost_hamiltonian(G)
    C_star = optimal_cut_value(G)
    history: list[float] = []
    total_nfev = 0

    # --- Stage 1: p=1 via grid + COBYLA -------------------------------------
    g1, b1, _ = grid_search_p1(G, grid_size=p1_grid_size)
    x = np.array([g1, b1], dtype=float)
    obj_p1 = _make_tracked_objective(G, H, p=1, history=history)
    res = minimize(obj_p1, x, method="COBYLA", tol=tol, options={"maxiter": max_iter})
    x = np.asarray(res.x, dtype=float)
    total_nfev += int(res.nfev)

    # --- Stages 2..p: warm-start + mini-grid + COBYLA -----------------------
    for q in range(2, p + 1):
        # Split current solution into gammas_prev (len q-1) and betas_prev (len q-1).
        gammas_prev = x[: q - 1].tolist()
        betas_prev = x[q - 1 :].tolist()

        g_new, b_new, _ = _grid_search_new_layer(
            G, p=q, gammas_prev=gammas_prev, betas_prev=betas_prev,
            grid_size=layer_grid_size,
        )

        # Assemble the 2q-vector x0 = [γ_1..γ_{q-1}, γ_q, β_1..β_{q-1}, β_q].
        x0 = np.concatenate([np.array(gammas_prev), [g_new],
                              np.array(betas_prev), [b_new]])
        obj_q = _make_tracked_objective(G, H, p=q, history=history)
        res = minimize(obj_q, x0, method="COBYLA", tol=tol, options={"maxiter": max_iter})
        x = np.asarray(res.x, dtype=float)
        total_nfev += int(res.nfev)

    gammas_final = x[:p].tolist()
    betas_final = x[p:].tolist()
    final_ev = _energy(G, H, p, gammas_final, betas_final)
    r = approximation_ratio(final_ev, C_star)

    return {
        "gammas": gammas_final,
        "betas": betas_final,
        "final_expectation": final_ev,
        "approximation_ratio": r,
        "n_iterations": total_nfev,
        "convergence_history": history,
        "wall_time_seconds": time.time() - t0,
    }


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from src.graph_generator import generate_3regular_graph, generate_triangle

    print("=" * 60)
    print("Module 5 demo — optimizer")
    print("=" * 60)

    K3 = generate_triangle()

    print("\n[1] K₃, p=1, grid search (grid_size=50):")
    g, b, ev = grid_search_p1(K3, grid_size=50)
    H = build_cost_hamiltonian(K3)
    r = approximation_ratio(ev, optimal_cut_value(K3))
    print(f"    γ*={g:.4f}  β*={b:.4f}")
    print(f"    ⟨H_C⟩ = {ev:+.6f}   r = {r:.6f}")

    print("\n[2] K₃, p=1, full optimize_qaoa:")
    res1 = optimize_qaoa(K3, p=1)
    print(f"    γ={[round(x,4) for x in res1['gammas']]}  β={[round(x,4) for x in res1['betas']]}")
    print(f"    ⟨H_C⟩ = {res1['final_expectation']:+.6f}   r = {res1['approximation_ratio']:.6f}")
    print(f"    nfev = {res1['n_iterations']}, history len = {len(res1['convergence_history'])}")
    print(f"    wall time = {res1['wall_time_seconds']:.3f} s")

    print("\n[3] K₃, p=2 layer-by-layer:")
    res2 = optimize_qaoa(K3, p=2)
    print(f"    γ={[round(x,4) for x in res2['gammas']]}  β={[round(x,4) for x in res2['betas']]}")
    print(f"    r(p=2) = {res2['approximation_ratio']:.6f}   "
          f"(p=1 was {res1['approximation_ratio']:.6f})")
    print(f"    wall time = {res2['wall_time_seconds']:.3f} s")

    print("\n[4] K₃, p=3:")
    res3 = optimize_qaoa(K3, p=3)
    print(f"    r(p=3) = {res3['approximation_ratio']:.6f}")
    print(f"    wall time = {res3['wall_time_seconds']:.3f} s")

    print("\n[5] Farhi bound check — 3-regular p=1 (seed=0):")
    print(f"    {'n':>3}  {'r':>8}   {'>= 0.6924?':>12}")
    for n in (4, 6, 8, 10):
        G = generate_3regular_graph(n, seed=0)
        res = optimize_qaoa(G, p=1)
        r = res['approximation_ratio']
        mark = "yes" if r >= 0.6924 else "NO"
        print(f"    {n:>3}  {r:>8.4f}   {mark:>12}")
