"""
Graph statistics, used to power summary.py.

We allow for arbitrary computation of any specific statistic on some graph,
computing more than necessary if we have dependencies. See the top level
`statistics_computation` dictionary for usage.
"""

import itertools
from statistics import median
from typing import Callable

import networkx as nx


def compute_degree(graph: nx.DiGraph) -> tuple[int, float]:
    """
    Computes the (max, median) degree of a `graph`.
    """
    # number_of_nodes is a cheap call
    if graph.number_of_nodes() == 0:
        return (0, 0.0)
    else:
        degrees = [deg for _, deg in graph.degree()]
        return max(degrees), median(degrees)

def compute_on_cc(directed_graph: nx.DiGraph) -> tuple[int, float]:
    graph: nx.Graph = directed_graph.to_undirected()
    cc = list(nx.connected_components(graph))
    # Save the max diameter
    # Use diameter only for components with ≥2 nodes (singleton components have diameter 0)
    diameters = [
        nx.diameter(graph.subgraph(c).copy()) if len(c) > 1 else 0
        for c in cc
    ]
    max_diameter = max(diameters, default=0)

    # Save the average path lengths
    # Compute average shortest path length only for components with ≥2 nodes (undefined for singletons, set to 0.0)
    avg_path_lengths = [
        nx.average_shortest_path_length(graph.subgraph(c).copy()) if len(c) > 1 else 0.0
        for c in cc
    ]

    if len(avg_path_lengths) != 0:
        avg_path_len = sum(avg_path_lengths) / len(avg_path_lengths)
    else:
        avg_path_len = 0.0

    return max_diameter, avg_path_len

# The type signature on here is quite bad. I would like to say that an n-tuple has n-outputs.
statistics_computation: dict[tuple[str, ...], Callable[[nx.DiGraph], tuple[float | int, ...]]] = {
    ('Number of nodes',): lambda graph : (graph.number_of_nodes(),),
    ('Number of edges',): lambda graph : (graph.number_of_edges(),),
    ('Number of connected components',): lambda graph : (nx.number_connected_components(graph.to_undirected()),),
    ('Density',): lambda graph : (nx.density(graph),),

    ('Max degree', 'Median degree'): compute_degree,
    ('Max diameter', 'Average path length'): compute_on_cc,
}

# All of the keys inside statistics_computation, flattened.
statistics_options: list[str] = list(itertools.chain(*(list(key) for key in statistics_computation.keys())))

def compute_statistics(graph: nx.DiGraph, statistics: list[str]) -> dict[str, float | int]:
    """
    Computes `statistics` for a graph corresponding to the top-level `statistics` dictionary
    in this file.
    """

    # early-scan cutoff for statistics:
    # we want to err as soon as possible
    for stat in statistics:
        if stat not in statistics_options:
            raise RuntimeError(f"Statistic {stat} not a computable statistics! Available statistics: {statistics_options}")

    # now, we can compute statistics only
    computed_statistics: dict[str, float | int] = dict()
    for statistic_tuple, compute in statistics_computation.items():
        # when we want them
        if not set(statistic_tuple).isdisjoint(set(statistics)):
            computed_tuple = compute(graph)
            assert len(statistic_tuple) == len(computed_tuple), f"bad tuple length for {statistic_tuple}"

            current_computed_statistics = zip(statistic_tuple, computed_tuple, strict=True)
            for stat, value in current_computed_statistics:
                computed_statistics[stat] = value

    # (and return only the statistics we wanted)
    return {key: computed_statistics[key] for key in statistics}
