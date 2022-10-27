import pytest
import shutil
from pathlib import Path
from src.mincostflow import MinCostFlow
from test.MEO.test_meo import OUT_FILE

TEST_DIR = 'test/MinCostFlow/'
OUT_FILE = TEST_DIR+'output/mincostflow-output.txt'

class TestMinCostFlow:
    def test_mincostflow_required(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)

        MinCostFlow.run(sources=TEST_DIR + 'input/sources.txt',
            targets=TEST_DIR + 'input/targets.txt',
            edges=TEST_DIR + 'input/edges.txt',
            output_file=OUT_FILE)
        assert out_path.exists()

    def test_mincostflow_missing_capacity(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)

        MinCostFlow.run(sources=TEST_DIR + 'input/sources.txt',
            targets=TEST_DIR + 'input/targets.txt',
            edges=TEST_DIR + 'input/edges.txt',
            output_file=OUT_FILE,
            flow=1)
        assert out_path.exists()

    def test_mincostflow_missing_flow(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)

        MinCostFlow.run(sources=TEST_DIR + 'input/sources.txt',
            targets=TEST_DIR + 'input/targets.txt',
            edges=TEST_DIR + 'input/edges.txt',
            output_file=OUT_FILE,
            capacity=1)
        assert out_path.exists()

    def test_mincostflow_all_optional(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Include all optional arguments
        MinCostFlow.run(sources=TEST_DIR + 'input/sources.txt',
            targets=TEST_DIR + 'input/targets.txt',
            edges=TEST_DIR + 'input/edges.txt',
            output_file=OUT_FILE,
            flow=1,
            capacity=1,
            singularity=False)
        assert out_path.exists()

    def test_mincostflow_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            MinCostFlow.run(sources=TEST_DIR + 'input/sources.txt',
                targets=TEST_DIR + 'input/targets.txt',
                output_file=OUT_FILE)
            
