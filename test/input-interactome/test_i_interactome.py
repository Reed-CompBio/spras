from pathlib import Path

from spras.dataset import Direction, GraphLoopiness, GraphMultiplicity, Interactome

INPUT_DIR = Path('test', 'input-interactome', 'input')

class TestInteractome:
    def test_get_directionality(self):
        assert Direction.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-directed.txt')) == Direction.DIRECTED
        assert Direction.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-undirected.txt')) == Direction.UNDIRECTED
        assert Direction.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-mixed.txt')) == Direction.MIXED

    def test_get_loops(self):
        assert GraphLoopiness.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-loopy.txt')) == GraphLoopiness.LOOPY
        assert GraphLoopiness.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-noloops.txt')) == GraphLoopiness.NO_LOOPS


    def test_get_multiplicity(self):
        assert GraphMultiplicity.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-multi.txt')) == GraphMultiplicity.MULTI
        assert GraphMultiplicity.from_interactome(Interactome.from_file(INPUT_DIR / 'interactome-simple.txt')) == GraphMultiplicity.SIMPLE
