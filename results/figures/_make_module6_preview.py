"""Module 6 sanity preview — plots the scaling study results.

Prefers the full 5-seed production study on disk
(`results/data/scaling_results.{csv,json}`) if present. Otherwise falls back
to a compact 3-seed run for quick iteration.

Layout: 2×2 grid showing
    (a) approximation ratio vs N, one line per p (mean ± std).
    (b) CNOT count vs N, one line per p.
    (c) circuit depth vs N, one line per p.
    (d) wall time per experiment vs N, one line per p.

Saved to results/figures/module6_scaling_preview.png at dpi=200.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from src.run_experiment import (
    aggregate_results,
    load_config,
    run_scaling_study,
    save_results,
)


FULL_RESULTS_JSON = Path("results/data/scaling_results.json")


def _line(ax, agg, ycol, ylabel, title, errcol=None):
    for p in sorted(agg["p"].unique()):
        sub = agg[agg["p"] == p].sort_values("n")
        if errcol is not None:
            ax.errorbar(sub["n"], sub[ycol], yerr=sub[errcol],
                        marker="o", capsize=3, label=f"p={p}")
        else:
            ax.plot(sub["n"], sub[ycol], marker="o", label=f"p={p}")
    ax.set_xlabel("N")
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)


def _load_or_run() -> tuple[pd.DataFrame, int]:
    """Return (raw df, seed count). Uses saved full study if available."""
    if FULL_RESULTS_JSON.exists():
        print(f"Loading full study from {FULL_RESULTS_JSON} ...")
        df = pd.read_json(FULL_RESULTS_JSON, orient="records")
        n_seeds = df["seed"].nunique()
        print(f"  loaded {len(df)} experiments ({n_seeds} seeds).")
        return df, n_seeds

    cfg = load_config()
    subset = {"graph_sizes": [3, 4, 6, 8, 10], "p_values": [1, 2, 3],
              "seeds": [0, 1, 2]}
    print("No full study on disk — running compact 3-seed preview ...")
    df = run_scaling_study(cfg, subset=subset, verbose=True)
    save_results(df, output_dir="results/data", stem="scaling_preview",
                 formats=("csv", "json"))
    return df, 3


def main() -> None:
    df, n_seeds = _load_or_run()
    agg = aggregate_results(df)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    _line(axes[0, 0], agg, "r_mean",
          "approximation ratio r",
          f"(a) r vs N  (mean ± std, {n_seeds} seeds)",
          errcol="r_std")
    axes[0, 0].axhline(0.6924, color="red", linestyle="--", linewidth=1,
                       label="Farhi 0.6924")
    axes[0, 0].set_ylim(0.6, 1.05)
    axes[0, 0].legend(fontsize=8)

    _line(axes[0, 1], agg, "cnot_mean", "CNOT count", "(b) CNOT vs N")
    _line(axes[1, 0], agg, "depth_mean", "depth", "(c) circuit depth vs N")
    _line(axes[1, 1], agg, "wall_time_mean", "wall time (s)",
          "(d) per-experiment wall time vs N")

    label = (f"full production study ({n_seeds} seeds, {len(df)} experiments)"
             if n_seeds >= 5 else f"compact {n_seeds}-seed run")
    fig.suptitle(f"Module 6 — scaling study sanity ({label})",
                 fontsize=13, y=1.00)
    fig.tight_layout()
    out = "results/figures/module6_scaling_preview.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"\nsaved -> {out}")

    print("\nAggregated summary:")
    print(agg.to_string(index=False))


if __name__ == "__main__":
    main()
