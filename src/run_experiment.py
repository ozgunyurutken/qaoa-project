"""
Module 6 — experiment orchestration.

Runs the full scaling grid

    (N, p, seed)  with  N ∈ config["graph_sizes"],
                         p ∈ config["p_values"],
                         seed ∈ config["seeds"]

against the QAOA pipeline (Modules 1–5) and produces a tidy pandas
DataFrame plus per-(N, p) aggregates.

Public API:
    load_config(path)                         -> dict
    run_single_experiment(n, p, seed, config) -> dict
    run_scaling_study(config, subset=None)    -> pd.DataFrame
    aggregate_results(df)                     -> pd.DataFrame
    save_results(df, output_dir, stem="scaling_results", formats=("csv","json"))
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
import yaml

from src.circuit import qaoa_circuit
from src.graph_generator import generate_3regular_graph, generate_triangle
from src.hamiltonian import optimal_cut_value
from src.metrics import gate_count
from src.optimizer import optimize_qaoa


DEFAULT_CONFIG_PATH = "configs/experiment_config.yaml"


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    """Load YAML config as a plain dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _graph_for(n: int, seed: int):
    """Return K₃ for n=3 (ignoring seed) or a 3-regular graph otherwise."""
    if n == 3:
        return generate_triangle()
    return generate_3regular_graph(n, seed=seed)


# ---------------------------------------------------------------------------
# Single experiment
# ---------------------------------------------------------------------------

def run_single_experiment(n: int, p: int, seed: int, config: dict) -> dict:
    """
    Run one (N, p, seed) experiment end-to-end.

    Returns
    -------
    dict with all per-experiment metrics — this is the row fed into the
    scaling DataFrame. `convergence_history` is included here (useful for
    notebook demos on single runs) but dropped by `run_scaling_study`
    before tabulating to keep the DataFrame compact.
    """
    opt_cfg = config.get("optimizer", {})
    grid_cfg = config.get("grid_search", {})

    G = _graph_for(n, seed)
    n_edges = G.number_of_edges()
    C_star = optimal_cut_value(G)

    t_start = time.time()
    res = optimize_qaoa(
        G,
        p=p,
        max_iter=opt_cfg.get("max_iter", 200),
        tol=float(opt_cfg.get("tol", 1e-6)),
        p1_grid_size=grid_cfg.get("p1_grid_size", 50),
        layer_grid_size=grid_cfg.get("layer_grid_size", 10),
    )
    wall_time = time.time() - t_start

    # Gate count on the final (transpiled) ansatz.
    qc_final = qaoa_circuit(G, p=p, gammas=res["gammas"], betas=res["betas"])
    gc = gate_count(qc_final, transpiled=True)

    return {
        "n": int(n),
        "p": int(p),
        "seed": int(seed),
        "n_edges": int(n_edges),
        "C_star": int(C_star),
        "final_expectation": float(res["final_expectation"]),
        "approximation_ratio": float(res["approximation_ratio"]),
        "gammas": list(res["gammas"]),
        "betas": list(res["betas"]),
        "gate_count": int(gc["total"]),
        "cnot_count": int(gc["cnot"]),
        "single_qubit_count": int(gc["single_qubit"]),
        "depth": int(gc["depth"]),
        "n_iterations": int(res["n_iterations"]),
        "wall_time_seconds": float(wall_time),
        # Keep for callers who want convergence curves on single runs;
        # `run_scaling_study` drops this before building the DataFrame.
        "convergence_history": list(res["convergence_history"]),
    }


# ---------------------------------------------------------------------------
# Full scaling study
# ---------------------------------------------------------------------------

def run_scaling_study(
    config: dict,
    subset: dict | None = None,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Run the full (N, p, seed) grid.

    Parameters
    ----------
    config
        Parsed YAML config.
    subset
        Optional overrides for which sizes/ps/seeds to iterate — useful for
        tests and quick experiments.  Accepted keys: `graph_sizes`,
        `p_values`, `seeds`. Any key present replaces the corresponding
        config entry for this call only.
    verbose
        If True, prints a one-line status per experiment.

    Returns
    -------
    pd.DataFrame with one row per experiment. `convergence_history` is
    dropped from the frame (still accessible via `run_single_experiment`).
    """
    ns = _coerce(config, subset, "graph_sizes")
    ps = _coerce(config, subset, "p_values")
    seeds = _coerce(config, subset, "seeds")

    rows: list[dict[str, Any]] = []
    total = len(ns) * len(ps) * len(seeds)
    k = 0
    for n in ns:
        for p in ps:
            for seed in seeds:
                k += 1
                row = run_single_experiment(n, p, seed, config)
                row.pop("convergence_history", None)
                rows.append(row)
                if verbose:
                    print(f"[{k:>3}/{total}] n={n} p={p} seed={seed} "
                          f"r={row['approximation_ratio']:.4f} "
                          f"t={row['wall_time_seconds']:.2f}s")
    return pd.DataFrame(rows)


def _coerce(config: dict, subset: dict | None, key: str) -> list:
    if subset is not None and key in subset:
        return list(subset[key])
    return list(config[key])


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate over seeds: mean/std/min/max per (N, p) for approximation
    ratio + means for wall time / iterations; circuit structural metrics
    (gate_count, cnot, depth) are identical across seeds for fixed (N, p)
    *shape* but seed affects the concrete graph — we still report the mean
    (and std, which should be ≈ 0 for K₃ and small but non-zero for
    3-regular random graphs since transpile output can vary).
    """
    grouped = df.groupby(["n", "p"], as_index=False).agg(
        r_mean=("approximation_ratio", "mean"),
        r_std=("approximation_ratio", "std"),
        r_min=("approximation_ratio", "min"),
        r_max=("approximation_ratio", "max"),
        cnot_mean=("cnot_count", "mean"),
        gate_mean=("gate_count", "mean"),
        depth_mean=("depth", "mean"),
        n_iter_mean=("n_iterations", "mean"),
        wall_time_mean=("wall_time_seconds", "mean"),
        n_seeds=("seed", "nunique"),
    )
    # With a single seed per group, pandas returns NaN for std — swap to 0.0.
    grouped["r_std"] = grouped["r_std"].fillna(0.0)
    return grouped


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def save_results(
    df: pd.DataFrame,
    output_dir: str | Path,
    stem: str = "scaling_results",
    formats: Iterable[str] = ("csv", "json"),
) -> dict[str, Path]:
    """
    Save `df` as CSV and/or JSON under `output_dir`.

    CSV gets lists (gammas, betas) JSON-stringified so round-trip is lossless.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    if "csv" in formats:
        df_csv = df.copy()
        for col in ("gammas", "betas"):
            if col in df_csv.columns:
                df_csv[col] = df_csv[col].apply(json.dumps)
        path_csv = out_dir / f"{stem}.csv"
        df_csv.to_csv(path_csv, index=False)
        paths["csv"] = path_csv

    if "json" in formats:
        path_json = out_dir / f"{stem}.json"
        df.to_json(path_json, orient="records", indent=2)
        paths["json"] = path_json

    return paths


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the QAOA MaxCut scaling study.")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, type=str,
                        help="Path to experiment_config.yaml")
    parser.add_argument("--small", action="store_true",
                        help="Run a small subset for a smoke test "
                             "(N∈{3,4}, p∈{1,2}, seeds∈{0,1}).")
    parser.add_argument("--no-save", action="store_true",
                        help="Do not write CSV/JSON to disk.")
    args = parser.parse_args()

    print("=" * 60)
    print("Module 6 demo — run_experiment")
    print("=" * 60)

    cfg = load_config(args.config)
    print(f"\nConfig: {args.config}")
    print(f"  graph_sizes = {cfg['graph_sizes']}")
    print(f"  p_values    = {cfg['p_values']}")
    print(f"  seeds       = {cfg['seeds']}")

    subset = None
    if args.small:
        subset = {"graph_sizes": [3, 4], "p_values": [1, 2], "seeds": [0, 1]}
        print(f"\nSmall subset override: {subset}")

    t0 = time.time()
    df = run_scaling_study(cfg, subset=subset, verbose=True)
    elapsed = time.time() - t0
    print(f"\nCompleted {len(df)} experiments in {elapsed:.1f}s "
          f"(avg {elapsed/len(df):.2f}s/exp).")

    print("\nPer-row results (columns):")
    print(df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.drop(columns=["gammas", "betas"]).head().to_string())

    agg = aggregate_results(df)
    print("\nAggregated over seeds:")
    print(agg.to_string(index=False))

    if not args.no_save:
        out_dir = cfg["output"]["data_dir"]
        stem = "scaling_small" if args.small else "scaling_results"
        paths = save_results(df, output_dir=out_dir, stem=stem,
                             formats=cfg["output"]["save_format"])
        print(f"\nSaved:")
        for fmt, p in paths.items():
            print(f"  {fmt} -> {p}")
