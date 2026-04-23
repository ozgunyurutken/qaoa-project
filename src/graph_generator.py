"""
Module 1 — Reproducible graph generation for QAOA experiments.

Scope:
    * K3 (triangle) is the presentation toy example (N=3, 2-regular).
    * N >= 4 uses random 3-regular graphs. Because a 3-regular graph on n
      nodes has 3n/2 edges, n must be even.

Public API:
    generate_triangle()
    generate_3regular_graph(n, seed)
    graph_summary(G)
"""
from __future__ import annotations

import networkx as nx


def generate_triangle() -> nx.Graph:
    """K3: complete graph on 3 nodes (2-regular triangle)."""
    return nx.complete_graph(3)


def generate_3regular_graph(n: int, seed: int) -> nx.Graph:
    """
    Generate a reproducible random 3-regular graph on `n` nodes.

    Parameters
    ----------
    n : int
        Number of nodes. Must be >= 3. For n >= 4, n must be even.
    seed : int
        PRNG seed forwarded to ``networkx.random_regular_graph``.

    Returns
    -------
    networkx.Graph
        * n == 3 -> K3 (triangle, 2-regular special case).
        * n >= 4 even -> random 3-regular graph.

    Raises
    ------
    ValueError
        If n < 3, or if n >= 5 and odd.
    """
    if n < 3:
        raise ValueError(f"n must be >= 3, got {n}")
    if n == 3:
        return generate_triangle()
    if n % 2 != 0:
        raise ValueError(
            "3-regular graph requires even n for n >= 4. "
            "Supported values: n in {3, 4, 6, 8, 10, 12, ...}"
        )
    return nx.random_regular_graph(d=3, n=n, seed=seed)


def graph_summary(G: nx.Graph) -> dict:
    """
    Compact structural summary for logging, tests, and notebooks.

    Returns
    -------
    dict with keys:
        n_nodes : int
        n_edges : int
        degrees : list[int]  (one entry per node, in node-id order)
        is_3regular : bool
    """
    degrees = [deg for _, deg in sorted(G.degree(), key=lambda x: x[0])]
    return {
        "n_nodes": G.number_of_nodes(),
        "n_edges": G.number_of_edges(),
        "degrees": degrees,
        "is_3regular": bool(degrees) and all(d == 3 for d in degrees),
    }


if __name__ == "__main__":
    # Quick demo: run with `python -m src.graph_generator`
    print("=" * 60)
    print("Module 1 demo — graph_generator")
    print("=" * 60)

    print("\n[1] K3 (triangle, N=3 toy example):")
    K3 = generate_triangle()
    print(f"    nodes = {list(K3.nodes())}")
    print(f"    edges = {list(K3.edges())}")
    print(f"    summary = {graph_summary(K3)}")

    print("\n[2] 3-regular graphs for the scaling study (seed=0):")
    for _n in (4, 6, 8, 10):
        _G = generate_3regular_graph(_n, seed=0)
        _s = graph_summary(_G)
        _edges = sorted(_G.edges())
        _preview = _edges[:6] + (["..."] if len(_edges) > 6 else [])
        print(
            f"    n={_n:<2}  |V|={_s['n_nodes']:<2} |E|={_s['n_edges']:<2}  "
            f"3-reg={_s['is_3regular']}  edges={_preview}"
        )

    print("\n[3] Seed reproducibility check (n=8):")
    _e_a = sorted(generate_3regular_graph(8, seed=42).edges())
    _e_b = sorted(generate_3regular_graph(8, seed=42).edges())
    print(f"    seed=42 twice -> identical? {_e_a == _e_b}")

    print("\n[4] Different seeds -> different graphs (n=8):")
    for _s in (0, 1, 2):
        _e = sorted(generate_3regular_graph(8, seed=_s).edges())
        print(f"    seed={_s}: first 4 edges = {_e[:4]}")

    print("\n[5] Error handling:")
    for _n in (5, 7, 2):
        try:
            generate_3regular_graph(_n, seed=0)
        except ValueError as _err:
            print(f"    n={_n} -> ValueError: {_err}")
