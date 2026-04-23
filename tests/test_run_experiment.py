"""Tests for Module 6: run_experiment."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.run_experiment import (
    aggregate_results,
    load_config,
    run_scaling_study,
    run_single_experiment,
    save_results,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fast_config() -> dict:
    """Minimal config usable for tests — small grids to keep runtime low."""
    return {
        "graph_sizes": [3, 4],
        "p_values": [1, 2],
        "seeds": [0, 1],
        "optimizer": {"method": "COBYLA", "tol": 1e-6, "max_iter": 100},
        "grid_search": {"p1_grid_size": 15, "layer_grid_size": 5},
        "output": {"data_dir": "results/data", "save_format": ["csv", "json"]},
    }


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_from_repo():
    cfg = load_config()
    for key in ("graph_sizes", "p_values", "seeds", "optimizer", "grid_search"):
        assert key in cfg
    assert cfg["graph_sizes"] == [3, 4, 6, 8, 10]
    assert cfg["p_values"] == [1, 2, 3]
    assert cfg["seeds"] == [0, 1, 2, 3, 4]


# ---------------------------------------------------------------------------
# run_single_experiment
# ---------------------------------------------------------------------------

def test_full_pipeline_k3(fast_config):
    """End-to-end run on K₃, p=1, seed=0 produces sensible output."""
    row = run_single_experiment(n=3, p=1, seed=0, config=fast_config)

    required = {
        "n", "p", "seed", "n_edges", "C_star",
        "final_expectation", "approximation_ratio",
        "gammas", "betas",
        "gate_count", "cnot_count", "single_qubit_count", "depth",
        "n_iterations", "wall_time_seconds", "convergence_history",
    }
    assert required.issubset(row.keys())

    # K₃ structural ground truths
    assert row["n"] == 3 and row["p"] == 1 and row["seed"] == 0
    assert row["n_edges"] == 3
    assert row["C_star"] == 2
    assert row["cnot_count"] == 6  # 2·|E|·p
    assert len(row["gammas"]) == 1 and len(row["betas"]) == 1

    # Optimization quality — K₃ p=1 should saturate at r = 1.
    assert row["approximation_ratio"] >= 0.95
    assert 0.0 <= row["approximation_ratio"] <= 1.0 + 1e-9
    assert np.isclose(row["final_expectation"],
                      -row["approximation_ratio"] * row["C_star"], atol=1e-9)

    # Sanity on meta
    assert row["n_iterations"] > 0
    assert row["wall_time_seconds"] > 0
    assert len(row["convergence_history"]) == row["n_iterations"]


def test_run_single_experiment_returns_plain_python_types(fast_config):
    """JSON round-trip must be trivial — no numpy scalars leaking through."""
    row = run_single_experiment(n=3, p=1, seed=0, config=fast_config)
    # Strip the embedded list fields, then check every leaf is plain.
    for key, value in row.items():
        if key in ("gammas", "betas", "convergence_history"):
            assert all(isinstance(v, float) for v in value)
        else:
            assert isinstance(value, (int, float)), f"{key} has type {type(value)}"


def test_run_single_experiment_k3_ignores_seed(fast_config):
    """K₃ is deterministic — seed changes should not change the graph or r."""
    r0 = run_single_experiment(3, 1, 0, fast_config)
    r1 = run_single_experiment(3, 1, 7, fast_config)
    assert r0["n_edges"] == r1["n_edges"] == 3
    # Same graph + same optimizer path ⇒ same r within float tolerance.
    assert np.isclose(r0["approximation_ratio"], r1["approximation_ratio"], atol=1e-9)


# ---------------------------------------------------------------------------
# run_scaling_study
# ---------------------------------------------------------------------------

def test_run_scaling_study_row_count(fast_config):
    """N=2 × p=2 × seed=2 = 8 rows."""
    df = run_scaling_study(fast_config)
    assert len(df) == 2 * 2 * 2
    assert set(df["n"].unique()) == {3, 4}
    assert set(df["p"].unique()) == {1, 2}
    assert set(df["seed"].unique()) == {0, 1}


def test_run_scaling_study_drops_convergence_history(fast_config):
    """The DataFrame must NOT contain convergence_history (saved separately)."""
    df = run_scaling_study(fast_config)
    assert "convergence_history" not in df.columns


def test_run_scaling_study_subset_override(fast_config):
    """`subset` kwarg must override config."""
    df = run_scaling_study(fast_config, subset={"graph_sizes": [3], "p_values": [1]})
    assert set(df["n"].unique()) == {3}
    assert set(df["p"].unique()) == {1}


def test_run_scaling_study_farhi_bound_holds(fast_config):
    """All rows with p=1 on the 3-regular sizes should clear Farhi 0.6924."""
    df = run_scaling_study(fast_config)
    p1_rows = df[df["p"] == 1]
    assert (p1_rows["approximation_ratio"] >= 0.6924).all()


# ---------------------------------------------------------------------------
# aggregate_results
# ---------------------------------------------------------------------------

def test_aggregate_columns(fast_config):
    df = run_scaling_study(fast_config)
    agg = aggregate_results(df)
    required = {"n", "p", "r_mean", "r_std", "r_min", "r_max",
                "cnot_mean", "gate_mean", "depth_mean",
                "n_iter_mean", "wall_time_mean", "n_seeds"}
    assert required.issubset(set(agg.columns))
    # 2 Ns × 2 ps = 4 groups
    assert len(agg) == 4


def test_aggregate_n_seeds_matches_config(fast_config):
    df = run_scaling_study(fast_config)
    agg = aggregate_results(df)
    assert (agg["n_seeds"] == 2).all()


def test_aggregate_r_range_ordering(fast_config):
    df = run_scaling_study(fast_config)
    agg = aggregate_results(df)
    assert (agg["r_min"] <= agg["r_mean"]).all()
    assert (agg["r_mean"] <= agg["r_max"]).all()


def test_aggregate_std_zero_when_single_seed(fast_config):
    """When group has only 1 row, std should be 0 (we fillna to 0)."""
    df = run_scaling_study(fast_config, subset={"seeds": [0]})
    agg = aggregate_results(df)
    assert (agg["r_std"] == 0.0).all()


# ---------------------------------------------------------------------------
# save_results (round-trip)
# ---------------------------------------------------------------------------

def test_save_results_writes_csv_and_json(fast_config, tmp_path):
    df = run_scaling_study(fast_config, subset={"graph_sizes": [3], "p_values": [1]})
    paths = save_results(df, output_dir=tmp_path, stem="test_out",
                         formats=("csv", "json"))
    assert paths["csv"].exists() and paths["csv"].suffix == ".csv"
    assert paths["json"].exists() and paths["json"].suffix == ".json"


def test_save_results_json_round_trip(fast_config, tmp_path):
    """JSON round-trip must preserve numeric fields exactly and lists as lists."""
    df = run_scaling_study(fast_config, subset={"graph_sizes": [3], "p_values": [1]})
    paths = save_results(df, output_dir=tmp_path, stem="rt", formats=("json",))
    loaded = json.loads(Path(paths["json"]).read_text())
    assert len(loaded) == len(df)
    first = loaded[0]
    assert isinstance(first["gammas"], list)
    assert isinstance(first["betas"], list)
    assert np.isclose(first["approximation_ratio"],
                      df.iloc[0]["approximation_ratio"], atol=1e-12)


def test_save_results_csv_round_trip(fast_config, tmp_path):
    """CSV round-trip: list columns stored as JSON strings, decode back cleanly."""
    df = run_scaling_study(fast_config, subset={"graph_sizes": [3], "p_values": [1]})
    paths = save_results(df, output_dir=tmp_path, stem="rt", formats=("csv",))
    reloaded = pd.read_csv(paths["csv"])
    # Decode stringified lists.
    for col in ("gammas", "betas"):
        reloaded[col] = reloaded[col].apply(json.loads)
    assert len(reloaded) == len(df)
    assert isinstance(reloaded.iloc[0]["gammas"], list)
    np.testing.assert_allclose(
        reloaded["approximation_ratio"].values,
        df["approximation_ratio"].values,
        atol=1e-9,
    )


def test_save_results_respects_formats(fast_config, tmp_path):
    df = run_scaling_study(fast_config, subset={"graph_sizes": [3], "p_values": [1]})
    paths = save_results(df, output_dir=tmp_path, stem="only_json", formats=("json",))
    assert "csv" not in paths
    assert "json" in paths


def test_save_results_creates_missing_dir(fast_config, tmp_path):
    target = tmp_path / "nested" / "dir"
    df = run_scaling_study(fast_config, subset={"graph_sizes": [3], "p_values": [1]})
    paths = save_results(df, output_dir=target, stem="out", formats=("json",))
    assert paths["json"].exists()


# ---------------------------------------------------------------------------
# Integration: full pipeline yields consistent values
# ---------------------------------------------------------------------------

def test_row_final_expectation_matches_ratio_formula(fast_config):
    """For every row: final_expectation == -approximation_ratio · C*."""
    df = run_scaling_study(fast_config)
    expected = -df["approximation_ratio"] * df["C_star"]
    np.testing.assert_allclose(df["final_expectation"].values, expected.values, atol=1e-9)


def test_row_gate_count_cnot_formula(fast_config):
    """2·|E|·p CNOT identity must hold on every row."""
    df = run_scaling_study(fast_config)
    expected = 2 * df["n_edges"] * df["p"]
    np.testing.assert_array_equal(df["cnot_count"].values, expected.values)
