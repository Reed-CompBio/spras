import shutil
from pathlib import Path

import pytest

from src.allpairs import AllPairs

TEST_DIR = 'test/AllPairs/'
OUT_DIR = TEST_DIR+'output/'

EXPECTED_DIR = TEST_DIR+'/expected/' 

class TestAllPairs:
    """
    Run all pairs shortest paths (AllPairs) tests in the Docker image
    """
    def test_allpairs(self):
        out_path = Path(OUT_DIR+'sample-out.txt')
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        AllPairs.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_DIR+'sample-out.txt'
        )
        assert out_path.exists()

    def test_allpairs_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            AllPairs.run(
                network=TEST_DIR + 'input/sample-in-net.txt',
                output_file=OUT_DIR+'sample-out.txt')


    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_allpairs_singularity(self):
        out_path = Path(OUT_DIR+'sample-out.txt')
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        AllPairs.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_DIR+'sample-out.txt',
            singularity=True
        )
        assert out_path.exists()

    def test_correctness(self):
        """
        Tests algorithm correctness of all_pairs_shortest_path.py by using AllPairs.run
        """
        out_path = Path(OUT_DIR+'correctness.txt')
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=TEST_DIR+'input/correctness-nodetypes.txt',
            network=TEST_DIR+'input/correctness-network.txt',
            output_file=OUT_DIR+'correctness.txt'
        )

        assert out_path.exists()

        with open(out_path, 'r') as f:
            edge_pairs = f.readlines()
        output_edges = []
        for edge in edge_pairs:
            node1, node2 = sorted(edge.split())
            output_edges.append((node1, node2))
        output_edges.sort()

        with open(EXPECTED_DIR+"correctness-expected.txt", 'r') as file:
            correctness_edge_pairs = file.readlines()
        correctness_edges = []
        for edge in correctness_edge_pairs:
            node1, node2 = edge.split()
            correctness_edges.append((node1, node2))

        assert output_edges == correctness_edges




