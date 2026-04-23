"""Builds the three notebooks programmatically — less painful than hand-editing JSON.

Run once after `src/visualizations.py` is in place to (re)generate:

    notebooks/01_k3_demo.ipynb
    notebooks/02_scaling_study.ipynb
    notebooks/03_visualizations.ipynb

The notebooks deliberately delegate to `src.visualizations` so that any plotting
logic lives in one place; cells stay short and focused on narrative.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

_counter = itertools.count(1)


def _cell_id(kind: str) -> str:
    return f"{kind}-{next(_counter):03d}"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "id": _cell_id("md"),
            "metadata": {}, "source": list(_join(lines))}


def code(*lines: str) -> dict:
    return {
        "cell_type": "code",
        "id": _cell_id("code"),
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": list(_join(lines)),
    }


def _join(lines):
    joined = "\n".join(lines)
    # Jupyter expects a list where each element ends with "\n" except the last.
    parts = joined.split("\n")
    return [p + ("\n" if i < len(parts) - 1 else "") for i, p in enumerate(parts)]


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python",
                            "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


# ---------------------------------------------------------------------------
# 01_k3_demo.ipynb — 6 cells per brief §3.2 Module 7
# ---------------------------------------------------------------------------

_SETUP_CHDIR = [
    "import os, sys",
    "from pathlib import Path",
    "# Move CWD to the project root so relative paths (configs/, results/) work",
    "# regardless of where the notebook is launched from.",
    "_here = Path.cwd()",
    "if _here.name == 'notebooks':",
    "    os.chdir(_here.parent)",
    "if str(Path.cwd()) not in sys.path:",
    "    sys.path.insert(0, str(Path.cwd()))",
    "print('cwd:', Path.cwd())",
]


nb_01 = notebook([
    md("# Notebook 01 — K₃ QAOA demo",
       "",
       "Step-by-step walkthrough of the QAOA pipeline on the triangle graph K₃ "
       "at p=1, following brief Section 3.2 (Module 7).  Each cell corresponds "
       "to one stage of the pipeline."),

    md("## Setup"),
    code(*_SETUP_CHDIR,
         "",
         "%load_ext autoreload",
         "%autoreload 2",
         "",
         "import numpy as np",
         "import matplotlib.pyplot as plt",
         "",
         "from src import visualizations as viz",
         "from src.graph_generator import generate_triangle",
         "from src.hamiltonian import build_cost_hamiltonian, optimal_cut_value",
         "from src.circuit import qaoa_circuit",
         "from src.metrics import approximation_ratio",
         "",
         "viz.setup_style()"),

    md("## Cell 1 — Generate K₃, show graph"),
    code("G = generate_triangle()",
         "print(f'nodes: {list(G.nodes())}')",
         "print(f'edges: {list(G.edges())}')",
         "print(f'optimal cut value C*: {optimal_cut_value(G)}')",
         "",
         "fig = viz.make_figure_09(n_3reg=6, seed_3reg=0)",
         "plt.show()"),

    md("## Cell 2 — Build H_C, print spectrum",
       "",
       "With Option 1 convention, eigenvalues of H_C are **-C(z)** — ground-state "
       "energy −C\\* = −2 for K₃."),
    code("from qiskit.quantum_info import Statevector",
         "",
         "H = build_cost_hamiltonian(G)",
         "print('H_C:')",
         "print(H)",
         "",
         "eigs = np.linalg.eigvalsh(H.to_matrix())",
         "print(f'\\neigenvalues: {sorted(eigs.round(6).tolist())}')",
         "print(f'ground-state energy: {eigs.min():.4f}  (should be -C* = -2)')"),

    md("## Cell 3 — Build circuit, visualize"),
    code("# Use the K3 detailed run to get optimal (γ*, β*) — picks up the cached objects.",
         "k3 = viz.collect_k3_detailed(grid_size=20, shots=5_000)",
         "print(f'γ* = {k3.gamma_opt:.4f},  β* = {k3.beta_opt:.4f}')",
         "",
         "fig = viz.make_figure_01(k3)",
         "plt.show()"),

    md("## Cell 4 — Optimize (grid + COBYLA), print parameters",
       "",
       "The grid-search → COBYLA path is executed inside `collect_k3_detailed`. "
       "We print the final values and report the expectation."),
    code("print(f'optimization finished after {len(k3.convergence)} COBYLA evaluations')",
         "print(f'final ⟨H_C⟩ = {k3.final_expectation:.6f}  (optimum = -{k3.c_star})')",
         "print(f'γ* = {k3.gamma_opt:.6f},  β* = {k3.beta_opt:.6f}')"),

    md("## Cell 5 — Histogram, optimization curve, landscape"),
    code("fig2 = viz.make_figure_02(k3); plt.show()",
         "fig3 = viz.make_figure_03(k3); plt.show()",
         "fig4 = viz.make_figure_04(k3); plt.show()"),

    md("## Cell 6 — Approximation ratio vs Farhi 2014 bound",
       "",
       "The Farhi bound 0.6924 applies only to **3-regular** graphs "
       "(K₃ is 2-regular, so the bound isn't formally applicable — we print it "
       "for reference)."),
    code("print(f'approximation ratio r = {k3.approx_ratio:.6f}')",
         "print(f'Farhi 2014 bound (3-regular p=1): r ≥ 0.6924')",
         "print(f'K₃ p=1 saturates at r = 1.0 in this implementation')",
         "",
         "# Sanity: uniform superposition baseline = 0.75 for K₃.",
         "print(f'\\nbaseline r for uniform superposition on K₃ = 0.75')"),
])


# ---------------------------------------------------------------------------
# 02_scaling_study.ipynb — 5 cells per brief
# ---------------------------------------------------------------------------

nb_02 = notebook([
    md("# Notebook 02 — Scaling study",
       "",
       "End-to-end scaling run across the full grid "
       "`N × p × seed = 5 × 3 × 5 = 75 experiments`.",
       "",
       "> **Runtime note:** on an M4 MacBook Air this takes ≈3–4 min. "
       "If the study is already on disk at `results/data/scaling_results.json`, "
       "re-running is optional — the aggregation cell works off the saved file."),

    md("## Cell 1 — Load config"),
    code(*_SETUP_CHDIR,
         "",
         "from src.run_experiment import load_config",
         "",
         "cfg = load_config()",
         "print(f'graph_sizes = {cfg[\"graph_sizes\"]}')",
         "print(f'p_values    = {cfg[\"p_values\"]}')",
         "print(f'seeds       = {cfg[\"seeds\"]}')"),

    md("## Cell 2 — Run full experiment grid",
       "",
       "Comment/uncomment the `run_scaling_study(...)` call depending on whether "
       "you want a fresh run or to load the saved one."),
    code("from pathlib import Path",
         "import pandas as pd",
         "from src.run_experiment import run_scaling_study",
         "",
         "saved = Path('results/data/scaling_results.json')",
         "if saved.exists():",
         "    print(f'loading {saved} ...')",
         "    df = pd.read_json(saved, orient='records')",
         "else:",
         "    print('running full scaling study (≈3 min) ...')",
         "    df = run_scaling_study(cfg, verbose=True)",
         "",
         "print(f'loaded {len(df)} experiments')",
         "df.head()"),

    md("## Cell 3 — Aggregate results"),
    code("from src.run_experiment import aggregate_results",
         "",
         "agg = aggregate_results(df)",
         "agg.round(4)"),

    md("## Cell 4 — Save CSVs"),
    code("from src.run_experiment import save_results",
         "",
         "paths = save_results(df, output_dir='results/data', stem='scaling_results',",
         "                     formats=('csv', 'json'))",
         "for fmt, p in paths.items():",
         "    print(f'{fmt:>4} -> {p}')",
         "",
         "agg_path = 'results/data/aggregated_results.csv'",
         "agg.to_csv(agg_path, index=False)",
         "print(f' csv -> {agg_path}')"),

    md("## Cell 5 — Summary table"),
    code("print('Per (N, p) summary (mean ± std across 5 seeds):')",
         "summary = agg[['n', 'p', 'r_mean', 'r_std', 'cnot_mean', 'depth_mean', 'n_seeds']]",
         "print(summary.to_string(index=False))",
         "",
         "# Farhi bound check — every 3-regular p=1 row must satisfy r ≥ 0.6924.",
         "p1_3reg = df[(df['p'] == 1) & (df['n'] >= 4)]",
         "assert (p1_3reg['approximation_ratio'] >= 0.6924).all()",
         "print(f'\\n✓ Farhi 2014 bound (r ≥ 0.6924) holds on all {len(p1_3reg)} 3-regular p=1 rows')"),
])


# ---------------------------------------------------------------------------
# 03_visualizations.ipynb — one cell per figure + final verify
# ---------------------------------------------------------------------------

_fig_cells = []
_figs = [
    ("01", "K₃ QAOA circuit diagram", "make_figure_01(k3)"),
    ("02", "K₃ measurement histogram (after QAOA)", "make_figure_02(k3)"),
    ("03", "K₃ optimization curve (⟨H_C⟩ vs iteration)", "make_figure_03(k3)"),
    ("04", "K₃ parameter landscape F(γ, β)", "make_figure_04(k3)"),
    ("05", "approximation ratio vs N (per p)", "make_figure_05(agg)"),
    ("06", "gate count vs N (total + CNOT, per p)", "make_figure_06(agg)"),
    ("07", "circuit depth vs N (per p)", "make_figure_07(agg)"),
    ("08", "approximation ratio vs p (selected N)", "make_figure_08(agg)"),
    ("09", "graph examples — K₃ + 3-regular N=6", "make_figure_09()"),
    ("10", "K₃ histogram — before vs after QAOA", "make_figure_10(k3)"),
]
_fig_stem = {
    "01": "01_k3_circuit_diagram", "02": "02_k3_measurement_histogram",
    "03": "03_k3_optimization_curve", "04": "04_k3_parameter_landscape",
    "05": "05_approximation_ratio_vs_n", "06": "06_gate_count_vs_n",
    "07": "07_depth_vs_n", "08": "08_approximation_ratio_vs_p",
    "09": "09_graph_examples", "10": "10_histogram_comparison",
}

for num, title, call in _figs:
    stem = _fig_stem[num]
    _fig_cells.append(md(f"## Figure {num} — {title}"))
    _fig_cells.append(code(
        f"fig = viz.{call}",
        f"paths = viz.save_fig(fig, '{stem}', 'results/figures')",
        f"plt.show()",
        f"print('saved:', paths)",
    ))

nb_03 = notebook([
    md("# Notebook 03 — Presentation figures",
       "",
       "Generates all 10 figures listed in brief Section 7 and saves each as "
       "PNG (dpi=300) + SVG under `results/figures/`."),

    md("## Setup"),
    code(*_SETUP_CHDIR,
         "",
         "%load_ext autoreload",
         "%autoreload 2",
         "",
         "import matplotlib.pyplot as plt",
         "import pandas as pd",
         "",
         "from src import visualizations as viz",
         "from src.run_experiment import aggregate_results",
         "",
         "viz.setup_style()",
         "",
         "# Pre-compute the two shared datasets:",
         "#   k3 — K₃ p=1 detailed run (for figures 01, 02, 03, 04, 10)",
         "#   agg — aggregated scaling results (for figures 05, 06, 07, 08)",
         "k3 = viz.collect_k3_detailed()",
         "df = pd.read_json('results/data/scaling_results.json', orient='records')",
         "agg = aggregate_results(df)",
         "print('k3 ready, agg rows:', len(agg))"),

    *_fig_cells,

    md("## Verify all 10 figures exist"),
    code("expected = [",
         "    '01_k3_circuit_diagram', '02_k3_measurement_histogram',",
         "    '03_k3_optimization_curve', '04_k3_parameter_landscape',",
         "    '05_approximation_ratio_vs_n', '06_gate_count_vs_n',",
         "    '07_depth_vs_n', '08_approximation_ratio_vs_p',",
         "    '09_graph_examples', '10_histogram_comparison',",
         "]",
         "missing = []",
         "for stem in expected:",
         "    for ext in ('png', 'svg'):",
         "        p = Path('results/figures') / f'{stem}.{ext}'",
         "        if not p.exists() or p.stat().st_size == 0:",
         "            missing.append(str(p))",
         "",
         "if missing:",
         "    print('MISSING:', missing)",
         "else:",
         "    print(f'✓ all {len(expected)} figures saved as PNG + SVG')",
         "assert not missing"),
])


def main() -> None:
    outdir = Path(__file__).parent
    outdir.mkdir(parents=True, exist_ok=True)
    for name, nb in [("01_k3_demo", nb_01),
                      ("02_scaling_study", nb_02),
                      ("03_visualizations", nb_03)]:
        path = outdir / f"{name}.ipynb"
        path.write_text(json.dumps(nb, indent=1))
        print(f"wrote {path}  ({len(nb['cells'])} cells)")


if __name__ == "__main__":
    main()
