import shutil
from pathlib import Path

import pytest

from src.allpairs import AllPairs

TEST_DIR = 'test/AllPairs/'
OUT_FILE = TEST_DIR+'output/out.txt'

EXPECTED_FILE = TEST_DIR+'/expected/out.txt' ## TODO not currently checked.

class TestAllPairs:
    """
    Run all pairs shortest paths (AllPairs) tests in the Docker image
    """
    def test_allpairs(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        AllPairs.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_FILE
        )
        assert out_path.exists()

    def test_allpairs_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            AllPairs.run(
                network=TEST_DIR + 'input/sample-in-net.txt',
                output_file=OUT_FILE)


    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_allpairs_singularity(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        AllPairs.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_FILE,
            singularity=True
        )
        assert out_path.exists()

    def test_correctness(self):
        """
        Tests algorithm correctness of all_pairs_shortest_path.py by using AllPairs.run
        """
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=TEST_DIR+'input/correctness-nodetypes.txt',
            network=TEST_DIR+'input/correctness-network.txt',
            output_file=OUT_FILE
        )

        assert out_path.exists()

        with open(out_path, 'r') as f:
            edge_pairs = f.readlines()
        output_edges = []
        for edge in edge_pairs:
            node1, node2 = sorted(edge.split())
            output_edges.append((node1, node2))
        output_edges.sort()

        expected_output = [
            ('A', 'B'),
            ('B', 'C'),
            ('C', 'D'),
        ]

        assert output_edges == expected_output



