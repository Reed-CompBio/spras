from pathlib import Path

import pytest

from spras.config.heuristics import GraphHeuristics, GraphHeuristicsError

FIXTURES_DIR = Path('test', 'heuristics', 'fixtures')

class TestHeuristics:
    def parse(self, heuristics: dict) -> GraphHeuristics:
        return GraphHeuristics.model_validate(heuristics)

    def test_nonempty(self):
        self.parse({ 'number_of_nodes': '>0', 'number_of_edges': '1' }
                   ).validate_graph_from_file(FIXTURES_DIR / 'nonempty.txt')

    def test_empty(self):
        self.parse({ 'number_of_nodes': '<1' }
                       ).validate_graph_from_file(FIXTURES_DIR / 'empty.txt')

        with pytest.raises(GraphHeuristicsError):
            self.parse({ 'number_of_nodes': '0<' }
                       ).validate_graph_from_file(FIXTURES_DIR / 'empty.txt')

    def test_undirected(self):
        self.parse({ 'number_of_nodes': '1 < x < 3', 'number_of_edges': 2 }
                    ).validate_graph_from_file(FIXTURES_DIR / 'undirected.txt')
