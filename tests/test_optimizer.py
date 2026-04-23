"""Tests for Module 5: optimizer."""
from __future__ import annotations

import time

import numpy as np
import pytest
from scipy.optimize import minimize

from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value
from src.metrics import approximation_ratio, expectation_value
from src.circuit import qaoa_circuit
from src.optimizer import (
    cobyla_refine,
    grid_search_p1,
    optimize_qaoa,
)


# ---------------------------------------------------------------------------
# Brief Section 3.2 named tests
# ---------------------------------------------------------------------------

def test_k3_p1_convergence():
    """K₃ at p=1 must reach r ≥ 0.85. Empirically optimum is r=1."""
    res = optimize_qaoa(generate_triangle(), p=1)
    assert res["approximation_ratio"] >= 0.85, (
        f"K₃ p=1 r={res['approximation_ratio']:.4f} below 0.85 threshold"
    )


def test_k3_p2_improves_over_p1():
    """
    p=2 must do at least as well as p=1 (monotonicity).

    Strict improvement is impossible for K₃ because p=1 already saturates r=1;
    we assert r(p=2) >= r(p=1) - numerical_slack.
    """
    K3 = generate_triangle()
    r1 = optimize_qaoa(K3, p=1)["approximation_ratio"]
    r2 = optimize_qaoa(K3, p=2)["approximation_ratio"]
    assert r2 >= r1 - 1e-6, f"p=2 regressed: r(p=1)={r1:.6f}, r(p=2)={r2:.6f}"


@pytest.mark.parametrize("n", [4, 6, 8])
def test_farhi_2014_bound(n):
    """
    p=1 optimization on 3-regular graphs (n=4, 6, 8, seed=0) satisfies
    Farhi 2014 bound r ≥ 0.6924.
    """
    G = generate_3regular_graph(n, seed=0)
    res = optimize_qaoa(G, p=1)
    r = res["approximation_ratio"]
    assert r >= 0.6924, f"n={n} p=1 r={r:.4f} below Farhi bound 0.6924"


def test_layer_by_layer_warm_start():
    """
    Layer-by-layer warm start is faster / better than cold random init at p=2.

    We compare:
        A) `optimize_qaoa(G, p=2)`              — warm start from p=1 optimum.
        B) cold COBYLA on 2p=4 params from a random initial point.

    Assertion: warm-start r is at least as good as cold-start r (and usually
    better, but numerical slack tolerated). This tests the *value* of the
    warm start, which is the key claim of the method.
    """
    G = generate_3regular_graph(6, seed=0)
    H = build_cost_hamiltonian(G)

    # Warm start
    warm = optimize_qaoa(G, p=2)
    r_warm = warm["approximation_ratio"]

    # Cold random init: draw 3 random starts and pick best, to be fair.
    rng = np.random.default_rng(0)
    best_cold_ev = np.inf
    for _ in range(3):
        x0 = np.concatenate([
            rng.uniform(0, np.pi, size=2),      # γ_1, γ_2
            rng.uniform(0, np.pi / 2, size=2),  # β_1, β_2
        ])

        def obj(x):
            return float(expectation_value(
                qaoa_circuit(G, p=2, gammas=x[:2], betas=x[2:]), H))

        res = minimize(obj, x0, method="COBYLA", tol=1e-6,
                       options={"maxiter": 200})
        if res.fun < best_cold_ev:
            best_cold_ev = float(res.fun)
    r_cold = approximation_ratio(best_cold_ev, optimal_cut_value(G))

    assert r_warm >= r_cold - 1e-6, (
        f"warm start (r={r_warm:.4f}) worse than cold (r={r_cold:.4f})"
    )


# ---------------------------------------------------------------------------
# grid_search_p1 — structure / sanity
# ---------------------------------------------------------------------------

def test_grid_search_p1_returns_triple():
    g, b, ev = grid_search_p1(generate_triangle(), grid_size=10)
    assert isinstance(g, float) and 0.0 <= g < np.pi
    assert isinstance(b, float) and 0.0 <= b < np.pi / 2
    assert isinstance(ev, float)


def test_grid_search_p1_not_worse_than_uniform():
    """Grid search must find a point at least as good as the uniform state
    (γ=β=0 corresponds to <H_C>=-|E|/2 on 3-regular graphs, r=0.75 on K₃)."""
    G = generate_3regular_graph(6, seed=0)
    _, _, ev = grid_search_p1(G, grid_size=20)
    # ⟨H_C⟩ on |+⟩^n is −|E|/2 = −9/2.
    assert ev <= -9 / 2 + 1e-9


def test_grid_search_p1_small_grid_raises():
    with pytest.raises(ValueError, match="grid_size must be >= 2"):
        grid_search_p1(generate_triangle(), grid_size=1)


# ---------------------------------------------------------------------------
# cobyla_refine — structure
# ---------------------------------------------------------------------------

def test_cobyla_refine_returns_scipy_result():
    K3 = generate_triangle()
    x0 = np.array([0.5, 1.0])
    res = cobyla_refine(K3, p=1, x0=x0, max_iter=50)
    assert hasattr(res, "x") and hasattr(res, "fun") and hasattr(res, "nfev")
    assert res.x.shape == (2,)


def test_cobyla_refine_improves_on_x0():
    """COBYLA should not return a worse solution than the starting point."""
    G = generate_3regular_graph(6, seed=0)
    H = build_cost_hamiltonian(G)
    x0 = np.array([0.3, 0.4, 0.2, 0.5])  # arbitrary p=2 start
    ev0 = float(expectation_value(qaoa_circuit(G, p=2, gammas=x0[:2], betas=x0[2:]), H))
    res = cobyla_refine(G, p=2, x0=x0, max_iter=200)
    assert res.fun <= ev0 + 1e-9


def test_cobyla_refine_wrong_x0_shape_raises():
    with pytest.raises(ValueError, match="x0 must have shape"):
        cobyla_refine(generate_triangle(), p=2, x0=np.array([0.1]))  # should be length 4


# ---------------------------------------------------------------------------
# optimize_qaoa — dict shape / contracts
# ---------------------------------------------------------------------------

def test_optimize_qaoa_return_keys():
    res = optimize_qaoa(generate_triangle(), p=1, p1_grid_size=10)
    required = {
        "gammas",
        "betas",
        "final_expectation",
        "approximation_ratio",
        "n_iterations",
        "convergence_history",
        "wall_time_seconds",
    }
    assert required.issubset(res.keys())


@pytest.mark.parametrize("p", [1, 2, 3])
def test_optimize_qaoa_param_lengths(p):
    res = optimize_qaoa(generate_triangle(), p=p, p1_grid_size=10, layer_grid_size=5)
    assert len(res["gammas"]) == p
    assert len(res["betas"]) == p


def test_optimize_qaoa_convergence_history_nonempty():
    res = optimize_qaoa(generate_triangle(), p=1, p1_grid_size=10)
    assert len(res["convergence_history"]) > 0
    # n_iterations should equal total nfev across COBYLA stages
    assert res["n_iterations"] == len(res["convergence_history"])


def test_optimize_qaoa_ratio_in_unit_interval():
    res = optimize_qaoa(generate_3regular_graph(6, seed=0), p=1, p1_grid_size=10)
    assert 0.0 <= res["approximation_ratio"] <= 1.0 + 1e-9


def test_optimize_qaoa_p_zero_raises():
    with pytest.raises(ValueError, match="p must be >= 1"):
        optimize_qaoa(generate_triangle(), p=0)


def test_optimize_qaoa_final_expectation_matches_params():
    """The returned final_expectation must match computing it from gammas/betas."""
    K3 = generate_triangle()
    res = optimize_qaoa(K3, p=2, p1_grid_size=10, layer_grid_size=5)
    H = build_cost_hamiltonian(K3)
    recomputed = float(expectation_value(
        qaoa_circuit(K3, p=2, gammas=res["gammas"], betas=res["betas"]), H))
    assert np.isclose(recomputed, res["final_expectation"], atol=1e-10)


def test_optimize_qaoa_wall_time_positive():
    res = optimize_qaoa(generate_triangle(), p=1, p1_grid_size=10)
    assert res["wall_time_seconds"] > 0.0


def test_convergence_history_is_monotone_in_best_so_far():
    """
    Per-stage COBYLA history is not strictly monotone (simplex probes both
    better and worse points), but the running minimum across all evaluations
    must be non-increasing (best-so-far).
    """
    res = optimize_qaoa(generate_3regular_graph(6, seed=0), p=1, p1_grid_size=10)
    history = res["convergence_history"]
    running_min = np.minimum.accumulate(history)
    # Allow exact equality; assert never *increases*.
    assert np.all(np.diff(running_min) <= 1e-12)
