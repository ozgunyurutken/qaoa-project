"""Tests for Module 7: visualizations."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

matplotlib.use("Agg")  # headless backend for CI/tests

from src import visualizations as viz
from src.run_experiment import aggregate_results, run_scaling_study


# ---------------------------------------------------------------------------
# Fixtures — small dataset that still exercises every figure codepath.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def small_df() -> pd.DataFrame:
    """2 Ns × 3 ps × 2 seeds = 12 rows, reusing the real pipeline."""
    fast_config = {
        "graph_sizes": [3, 4],
        "p_values": [1, 2, 3],
        "seeds": [0, 1],
        "optimizer": {"method": "COBYLA", "tol": 1e-6, "max_iter": 100},
        "grid_search": {"p1_grid_size": 15, "layer_grid_size": 5},
    }
    return run_scaling_study(fast_config)


@pytest.fixture(scope="module")
def small_agg(small_df) -> pd.DataFrame:
    return aggregate_results(small_df)


@pytest.fixture(scope="module")
def k3() -> viz.K3Detailed:
    """Fast K₃ detailed run (grid=10) — shared across tests."""
    return viz.collect_k3_detailed(grid_size=10, shots=2_000)


# ---------------------------------------------------------------------------
# setup_style
# ---------------------------------------------------------------------------

def test_setup_style_sets_serif():
    viz.setup_style()
    import matplotlib.pyplot as plt
    assert plt.rcParams["font.family"] == ["serif"]
    assert plt.rcParams["font.size"] >= 12


# ---------------------------------------------------------------------------
# save_fig round-trip
# ---------------------------------------------------------------------------

def test_save_fig_writes_png_and_svg(tmp_path):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    paths = viz.save_fig(fig, "probe", tmp_path)
    assert paths["png"].exists() and paths["png"].stat().st_size > 0
    assert paths["svg"].exists() and paths["svg"].stat().st_size > 0
    assert paths["png"].suffix == ".png"
    assert paths["svg"].suffix == ".svg"
    plt.close(fig)


# ---------------------------------------------------------------------------
# collect_k3_detailed — numerical sanity
# ---------------------------------------------------------------------------

def test_collect_k3_detailed_shapes(k3):
    assert k3.n == 3
    assert k3.c_star == 2
    assert k3.landscape_F.shape == (k3.grid_size, k3.grid_size)
    assert k3.landscape_gammas.shape == (k3.grid_size,)
    assert k3.landscape_betas.shape == (k3.grid_size,)


def test_collect_k3_detailed_optimal(k3):
    # K₃ p=1 should saturate at r=1 (within optimizer tolerance).
    assert k3.approx_ratio >= 0.99
    # final_expectation ≈ -C* = -2.
    assert np.isclose(k3.final_expectation, -2.0, atol=1e-3)


def test_collect_k3_detailed_histograms_sum_to_one(k3):
    assert abs(sum(k3.histogram_uniform.values()) - 1.0) < 1e-9
    assert abs(sum(k3.histogram_optimized.values()) - 1.0) < 1e-9


def test_collect_k3_detailed_optimized_peaks_on_cuts(k3):
    # The 6 optimal bitstrings (not 000, 111) should collectively hold > 0.9 mass.
    optimal = {"001", "010", "011", "100", "101", "110"}
    p_opt = sum(prob for b, prob in k3.histogram_optimized.items() if b in optimal)
    assert p_opt > 0.90


def test_collect_k3_detailed_cold_convergence_descends(k3):
    """Cold-start COBYLA must start suboptimal and end at −C* = −2."""
    assert len(k3.cold_convergence) > 0
    first = k3.cold_convergence[0]
    best = min(k3.cold_convergence)
    # Starting from (0.20, 0.20) is far from optimum → first eval well above −2.
    assert first > -1.5, f"cold start first eval {first} looks too optimal"
    # Best-so-far must reach the optimum within tolerance.
    assert best <= -1.99, f"cold COBYLA failed to reach −C*: best={best}"
    # Sanity on the stored cold_start pair.
    assert len(k3.cold_start) == 2
    assert 0.0 <= k3.cold_start[0] <= np.pi
    assert 0.0 <= k3.cold_start[1] <= np.pi / 2


# ---------------------------------------------------------------------------
# K3 detailed → JSON round-trip
# ---------------------------------------------------------------------------

def test_k3_to_json_dict_is_serializable(k3, tmp_path):
    payload = k3.to_json_dict()
    out = tmp_path / "k3.json"
    out.write_text(json.dumps(payload))
    loaded = json.loads(out.read_text())
    assert loaded["n"] == 3 and loaded["c_star"] == 2
    assert len(loaded["landscape_F"]) == k3.grid_size
    assert len(loaded["landscape_F"][0]) == k3.grid_size
    assert abs(sum(loaded["histogram_optimized"].values()) - 1.0) < 1e-9
    assert len(loaded["cold_convergence_history"]) == len(k3.cold_convergence)
    assert len(loaded["cold_start"]) == 2


# ---------------------------------------------------------------------------
# Figure factories — each returns a Figure without raising.
# ---------------------------------------------------------------------------

def test_make_figure_01(k3):
    fig = viz.make_figure_01(k3)
    assert isinstance(fig, Figure)


def test_make_figure_02(k3):
    fig = viz.make_figure_02(k3)
    assert isinstance(fig, Figure)


def test_make_figure_03(k3):
    fig = viz.make_figure_03(k3)
    assert isinstance(fig, Figure)


def test_make_figure_04(k3):
    fig = viz.make_figure_04(k3)
    assert isinstance(fig, Figure)


def test_make_figure_05(small_agg):
    fig = viz.make_figure_05(small_agg)
    assert isinstance(fig, Figure)


def test_make_figure_06(small_agg):
    fig = viz.make_figure_06(small_agg)
    assert isinstance(fig, Figure)


def test_make_figure_07(small_agg):
    fig = viz.make_figure_07(small_agg)
    assert isinstance(fig, Figure)


def test_make_figure_08(small_agg):
    fig = viz.make_figure_08(small_agg, ns=(3, 4))
    assert isinstance(fig, Figure)


def test_make_figure_09():
    fig = viz.make_figure_09(n_3reg=6, seed_3reg=0)
    assert isinstance(fig, Figure)


def test_make_figure_10(k3):
    fig = viz.make_figure_10(k3)
    assert isinstance(fig, Figure)


# ---------------------------------------------------------------------------
# generate_all end-to-end (uses a small hand-built scaling file).
# ---------------------------------------------------------------------------

def test_generate_all_raises_if_scaling_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        viz.generate_all(outdir=tmp_path, scaling_json=tmp_path / "missing.json")


def test_generate_all_produces_every_figure(tmp_path, small_df, monkeypatch):
    scaling_json = tmp_path / "scaling.json"
    small_df.to_json(scaling_json, orient="records", indent=2)

    # Redirect data artifact paths into tmp_path so tests don't touch repo files.
    monkeypatch.setattr(viz, "DEFAULT_DATA_DIR", tmp_path)
    outdir = tmp_path / "figs"
    paths = viz.generate_all(outdir=outdir, scaling_json=scaling_json,
                             verbose=False)

    # 10 figures, each with PNG+SVG.
    expected_stems = {
        "01_k3_circuit_diagram", "02_k3_measurement_histogram",
        "03_k3_optimization_curve", "04_k3_parameter_landscape",
        "05_approximation_ratio_vs_n", "06_gate_count_vs_n",
        "07_depth_vs_n", "08_approximation_ratio_vs_p",
        "09_graph_examples", "10_histogram_comparison",
    }
    for stem in expected_stems:
        png = outdir / f"{stem}.png"
        svg = outdir / f"{stem}.svg"
        assert png.exists() and png.stat().st_size > 0, f"missing {png}"
        assert svg.exists() and svg.stat().st_size > 0, f"missing {svg}"

    # Data artifacts
    assert paths["k3_json"]["json"].exists()
    assert paths["aggregated_csv"]["csv"].exists()
    agg = pd.read_csv(paths["aggregated_csv"]["csv"])
    assert {"n", "p", "r_mean", "r_std"}.issubset(agg.columns)
