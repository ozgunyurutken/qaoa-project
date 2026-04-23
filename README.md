# QAOA MaxCut — Scaling Study (BBL540E)

Course presentation implementation for **BBL540E: Quantum Data Structures & Algorithms** (İTÜ, Doç. Dr. Deniz Türkpençe).

This project implements the Quantum Approximate Optimization Algorithm (QAOA) for MaxCut on random 3-regular graphs and produces a scaling study across `N ∈ {3, 4, 6, 8, 10}` and `p ∈ {1, 2, 3}`.

- **Main toy example:** 3-node triangle (K₃), p=1 — walked through step by step in the presentation.
- **Scaling study:** 5 graph sizes × 3 p-values × 5 seeds = 75 runs.
- **Backend:** Local statevector simulation (no real hardware).
- **Convention:** Option 1 (minimization form) — `H_C = (1/2) Σ (Z_i Z_j − I)`.

Theoretical foundations: `docs/Phase_2.1_*.md` through `docs/Phase_2.7_*.md`. A 10-minute course presentation (Beamer PDF + LaTeX source) lives in `presentation/`.

---

## Setup

Requirements: Python ≥ 3.10.

```bash
# Create virtual env
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

## Running

```bash
# Run tests (154 cases, full suite should pass)
pytest

# Run the full 75-experiment scaling study (writes to results/data/)
python -m src.run_experiment --config configs/experiment_config.yaml

# Regenerate the 10 presentation figures from saved results
python -m src.visualizations
```

## Project Layout

```
qaoa-project/
├── src/                          # implementation modules
│   ├── graph_generator.py        # reproducible 3-regular graphs
│   ├── hamiltonian.py            # H_C, H_B, classical cut values
│   ├── circuit.py                # QAOA ansatz construction
│   ├── metrics.py                # expectation, ratio, gate count
│   ├── optimizer.py              # grid search + COBYLA (layer-by-layer warm start)
│   ├── run_experiment.py         # full scaling study orchestration
│   └── visualizations.py         # 10 presentation figures + style
├── tests/                        # pytest suites (one per module)
├── notebooks/                    # K₃ demo, scaling study, visualisations
├── configs/experiment_config.yaml
├── results/
│   ├── data/                     # CSV + JSON outputs (75-experiment dataset)
│   └── figures/                  # PNG + SVG plots (10 figures, dpi=300)
├── presentation/                 # LaTeX Beamer deck + compiled PDF
└── docs/                         # Phase 2 theoretical reference
```

## Presentation

The compiled deck is at [`presentation/qaoa_maxcut_presentation.pdf`](presentation/qaoa_maxcut_presentation.pdf). To rebuild from source:

```bash
cd presentation && ./build.sh
```

Requires a TeX Live installation with the `beamer`, `metropolis`, and `tikz` packages.
