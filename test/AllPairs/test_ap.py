import filecmp
import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.allpairs import AllPairs

# Note that we don't directly use the config in the test, but we need the config
# to be initialized under the hood nonetheless. Initializing the config has implications
# like setting hash length behaviors, container registries, etc.
config.init_from_file("config/config.yaml")

TEST_DIR = 'test/AllPairs/'
OUT_DIR = TEST_DIR+'output/'
EXPECTED_DIR = TEST_DIR+'expected/'


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
            output_file=str(out_path)
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
            output_file=str(out_path),
            container_framework="singularity")
        assert out_path.exists()

    def test_allpairs_correctness(self):
        """
        Tests algorithm correctness of all_pairs_shortest_path.py by using AllPairs.run
        The shortest paths are:
        A-B-C
        A-E
        B-C
        B-A-E
        so the union of the unique edges in these paths will be returned as the pathway.
        """
        out_path = Path(OUT_DIR+'correctness-out.txt')
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=TEST_DIR+'input/correctness-nodetypes.txt',
            network=TEST_DIR+'input/correctness-network.txt',
            output_file=OUT_DIR+'correctness-out.txt'
        )
        assert out_path.exists()

        with open(out_path, 'r') as f:
            edge_pairs = f.readlines()
        output_edges = []
        for edge in edge_pairs:
            node1, node2 = sorted(edge.split())
            output_edges.append((node1, node2))
        output_edges.sort()

        with open(EXPECTED_DIR+'correctness-expected.txt', 'r') as f:
            c_edge_pairs = f.readlines()
        correct_edges = []
        for edge in c_edge_pairs:
            node1, node2 = edge.split()
            correct_edges.append((node1, node2))

        assert output_edges == correct_edges

    def test_allpairs_zero_length(self):
        """
        Tests algorithm correctness of all_pairs_shortest_path.py by using AllPairs.run
        The test case has a single soucre and target that is the same node, so the only path has
        zero length.
        Therefore, the output pathway has no edges.
        """
        out_path = Path(OUT_DIR+'zero-length-out.txt')
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=TEST_DIR+'input/zero-length-nodetypes.txt',
            network=TEST_DIR+'input/zero-length-network.txt',
            output_file=OUT_DIR+'zero-length-out.txt'
        )

        assert filecmp.cmp(OUT_DIR+'zero-length-out.txt', EXPECTED_DIR+'zero-length-expected.txt', shallow=False)
