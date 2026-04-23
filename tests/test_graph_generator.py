"""Tests for Module 1: graph_generator."""
from __future__ import annotations

import networkx as nx
import pytest

from src.graph_generator import (
    generate_3regular_graph,
    generate_triangle,
    graph_summary,
)


# ---------------------------------------------------------------------------
# Triangle (K3) properties
# ---------------------------------------------------------------------------

def test_triangle_properties():
    """K3: 3 nodes, 3 edges, every node has degree 2, connected."""
    G = generate_triangle()
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 3
    degrees = [deg for _, deg in G.degree()]
    assert degrees == [2, 2, 2]
    assert nx.is_connected(G)


def test_generate_3regular_n3_returns_triangle():
    """n=3 special case: generator returns K3 (bypassing the 3-regular rule)."""
    G = generate_3regular_graph(3, seed=0)
    assert G.number_of_nodes() == 3
    assert G.number_of_edges() == 3
    assert [deg for _, deg in G.degree()] == [2, 2, 2]


# ---------------------------------------------------------------------------
# 3-regular graphs for the scaling study
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [4, 6, 8, 10])
def test_3regular_even_n(n: int):
    """For even n >= 4, generator produces a valid 3-regular graph."""
    G = generate_3regular_graph(n, seed=0)
    assert G.number_of_nodes() == n
    # 3-regular => |E| = 3n/2
    assert G.number_of_edges() == 3 * n // 2
    degrees = [deg for _, deg in G.degree()]
    assert all(d == 3 for d in degrees), f"Expected all nodes degree 3, got {degrees}"


@pytest.mark.parametrize("n", [5, 7, 9])
def test_3regular_odd_n_raises(n: int):
    """Odd n >= 5 is invalid for 3-regular (n*3/2 not integer)."""
    with pytest.raises(ValueError, match="3-regular graph requires even n"):
        generate_3regular_graph(n, seed=0)


def test_n_less_than_3_raises():
    """n < 3 is rejected (MaxCut on fewer than 3 nodes is trivial/ill-posed here)."""
    with pytest.raises(ValueError, match="n must be >= 3"):
        generate_3regular_graph(2, seed=0)


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n", [4, 6, 8, 10])
def test_seed_reproducibility(n: int):
    """Same seed must yield identical edge set."""
    G1 = generate_3regular_graph(n, seed=42)
    G2 = generate_3regular_graph(n, seed=42)
    assert set(G1.edges()) == set(G2.edges())


def test_different_seeds_produce_different_graphs():
    """Different seeds should (almost always) yield different edge sets.

    We test n=8 across several seeds; nearly all pairs should differ.
    """
    base = generate_3regular_graph(8, seed=0)
    differences = 0
    for s in [1, 2, 3, 4, 5]:
        other = generate_3regular_graph(8, seed=s)
        if set(base.edges()) != set(other.edges()):
            differences += 1
    assert differences >= 3, (
        "Expected at least 3 out of 5 alternate seeds to yield a different graph; "
        f"got {differences}"
    )


# ---------------------------------------------------------------------------
# graph_summary
# ---------------------------------------------------------------------------

def test_graph_summary_triangle():
    summary = graph_summary(generate_triangle())
    assert summary["n_nodes"] == 3
    assert summary["n_edges"] == 3
    assert summary["degrees"] == [2, 2, 2]
    assert summary["is_3regular"] is False  # K3 is 2-regular


def test_graph_summary_3regular():
    summary = graph_summary(generate_3regular_graph(6, seed=0))
    assert summary["n_nodes"] == 6
    assert summary["n_edges"] == 9
    assert summary["is_3regular"] is True
    assert all(d == 3 for d in summary["degrees"])
