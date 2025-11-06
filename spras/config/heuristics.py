import os

import networkx as nx
from pydantic import BaseModel, ConfigDict

from spras.interval import Interval
from spras.statistics import compute_statistics, statistics_options


class GraphHeuristicError(RuntimeError):
    """
    Represents an error arising from a graph algorithm output
    not meeting the necessary graph heuristisc.
    """
    failed_heuristics: list[tuple[str, float | int, list[Interval]]]

    @staticmethod
    def to_string(failed_heuristics: list[tuple[str, float | int, list[Interval]]]):
        return f"The following heuristics failed: {failed_heuristics}"

    def __init__(self, failed_heuristics: list[tuple[str, float | int, list[Interval]]]):
        super().__init__(GraphHeuristicError.to_string(failed_heuristics))

        self.failed_heuristics = failed_heuristics

    def __str__(self) -> str:
        return GraphHeuristicError.to_string(self.failed_heuristics)

class GraphHeuristics(BaseModel):
    number_of_nodes: Interval | list[Interval] = []
    number_of_edges: Interval | list[Interval] = []
    number_of_connected_components: Interval | list[Interval] = []
    density: Interval | list[Interval] = []

    max_degree: Interval | list[Interval] = []
    median_degree: Interval | list[Interval] = []
    max_diameter: Interval | list[Interval] = []
    average_path_length: Interval | list[Interval] = []

    def validate_graph(self, graph: nx.DiGraph):
        statistics_dictionary = {
            'Number of nodes': self.number_of_nodes,
            'Number of edges': self.number_of_edges,
            'Number of connected components': self.number_of_connected_components,
            'Density': self.density,
            'Max degree': self.max_degree,
            'Median degree': self.median_degree,
            'Max diameter': self.max_diameter,
            'Average path length': self.average_path_length
        }

        # quick assert: is statistics_dictionary exhaustive?
        assert set(statistics_dictionary.keys()) == set(statistics_options)

        stats = compute_statistics(
            graph,
            list(k for k, v in statistics_dictionary.items() if isinstance(v, list) and len(v) == 0)
        )

        failed_heuristics: list[tuple[str, float | int, list[Interval]]] = []
        for key, value in stats.items():
            intervals = statistics_dictionary[key]
            if not isinstance(intervals, list): intervals = [intervals]

            for interval in intervals:
                if interval.mem(value):
                    failed_heuristics.append((key, value, intervals))
                    break

        if len(failed_heuristics) != 0:
            raise GraphHeuristicError(failed_heuristics)

    model_config = ConfigDict(extra='forbid')

    def validate_graph_from_file(self, path: str | os.PathLike):
        # TODO: re-use from summary.py once we have a mixed/hypergraph library
        G = nx.read_edgelist(path, data=(('weight', float), ('Direction', str)), create_using=nx.DiGraph)

        # We explicitly use `list` here to stop add_edge
        # from expanding our iterator infinitely.
        for source, target, data in list(G.edges(data=True)):
            if data["Direction"] == 'U':
                G.add_edge(target, source, data)
            pass

        return self.validate_graph(G)
