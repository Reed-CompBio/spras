from pathlib import Path
from spras.analysis.visjs import visualize
import filecmp

EXAMPLE_INTERACTOME = Path('test', 'analysis', 'input', 'example_output.txt')
EXPECTED_VISJS = Path('test', 'analysis', 'expected_output', 'expected_visjs.html')

class TestCytoscape:
    def test_correctness(self):
        visjs_output = visualize(EXAMPLE_INTERACTOME)

        assert EXPECTED_VISJS.read_text().strip() == visjs_output.strip()
