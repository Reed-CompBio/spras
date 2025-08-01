import filecmp
import shutil
from pathlib import Path

import pytest

import spras.config.config as config
from spras.allpairs import AllPairs

# Note that we don't directly use the config in the test, but we need the config
# to be initialized under the hood nonetheless. Initializing the config has implications
# like setting hash length behaviors, container registries, etc.
config.init_from_file("config/config.yaml")

TEST_DIR = Path('test/AllPairs/')
OUT_DIR = TEST_DIR / 'output'
EXPECTED_DIR = TEST_DIR / 'expected'

def edge_equality_test_util(out_path: Path, expected_path: Path):
    assert out_path.exists(), "out path does not exist!"
    assert expected_path.exists(), "expected path does not exist!"

    with open(out_path, 'r') as f:
        edge_pairs = f.readlines()
    output_edges = []
    for edge in edge_pairs:
        node1, node2 = sorted(edge.split())
        output_edges.append((node1, node2))
    output_edges.sort()

    with open(expected_path, 'r') as f:
        c_edge_pairs = f.readlines()
    correct_edges = []
    for edge in c_edge_pairs:
        node1, node2 = edge.split()
        correct_edges.append((node1, node2))

    assert output_edges == correct_edges, "output edges are not exactly equal to the correct edges!"

class TestAllPairs:
    """
    Run all pairs shortest paths (AllPairs) tests in the Docker image
    """
    def test_allpairs(self):
        out_path = OUT_DIR.joinpath('sample-out.txt')
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        AllPairs.run(
            nodetypes=str(TEST_DIR / 'input' / 'sample-in-nodetypes.txt'),
            network=str(TEST_DIR / 'input' / 'sample-in-net.txt'),
            directed_flag=str(TEST_DIR / 'input' / 'directed-flag-false.txt'),
            output_file=str(out_path)
        )
        assert out_path.exists()

    def test_allpairs_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            AllPairs.run(
                network=str(TEST_DIR / 'input' / 'sample-in-net.txt'),
                output_file=str(OUT_DIR / 'sample-out.txt'))

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_allpairs_singularity(self):
        out_path = OUT_DIR / 'sample-out.txt'
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        AllPairs.run(
            nodetypes=str(TEST_DIR / 'input' / 'sample-in-nodetypes.txt'),
            network=str(TEST_DIR / 'input' / 'sample-in-net.txt'),
            directed_flag=str(TEST_DIR / 'input' / 'directed-flag-false.txt'),
            output_file=str(out_path),
            container_framework="singularity")
        assert out_path.exists()

    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_allpairs_singularity_unpacked(self):
        out_path = OUT_DIR / 'sample-out-unpack.txt'
        out_path.unlink(missing_ok=True)
        # Indicate via config mechanism that we want to unpack the Singularity container
        config.config.unpack_singularity = True
        AllPairs.run(
            nodetypes=str(TEST_DIR / 'input/sample-in-nodetypes.txt'),
            network=str(TEST_DIR / 'input/sample-in-net.txt'),
            directed_flag=str(TEST_DIR / 'input' / 'directed-flag-false.txt'),
            output_file=str(out_path),
            container_framework="singularity")
        config.config.unpack_singularity = False
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
        out_path = OUT_DIR / 'correctness-out.txt'
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=str(TEST_DIR / 'input' / 'correctness-nodetypes.txt'),
            network=str(TEST_DIR / 'input' / 'correctness-network.txt'),
            directed_flag=str(TEST_DIR / 'input' / 'directed-flag-false.txt'),
            output_file=str(OUT_DIR / 'correctness-out.txt')
        )

        edge_equality_test_util(out_path, EXPECTED_DIR / 'correctness-expected.txt')

    def test_allpairs_directed(self):
        out_path = OUT_DIR / 'directed-out.txt'
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=str(TEST_DIR / 'input' / 'directed-nodetypes.txt'),
            network=str(TEST_DIR / 'input' / 'directed-network.txt'),
            directed_flag=str(TEST_DIR / 'input' / 'directed-flag-true.txt'),
            output_file=str(OUT_DIR / 'directed-out.txt'),
        )

        edge_equality_test_util(out_path, EXPECTED_DIR.joinpath('directed-expected.txt'))

    def test_allpairs_zero_length(self):
        """
        Tests algorithm correctness of all_pairs_shortest_path.py by using AllPairs.run
        The test case has a single source and target that is the same node, so the only path has
        zero length.
        Therefore, the output pathway has no edges.
        """
        out_path = OUT_DIR / 'zero-length-out.txt'
        out_path.unlink(missing_ok=True)

        AllPairs.run(
            nodetypes=TEST_DIR / 'input' / 'zero-length-nodetypes.txt',
            network=TEST_DIR / 'input' / 'zero-length-network.txt',
            directed_flag=str(TEST_DIR / 'input' / 'directed-flag-false.txt'),
            output_file=OUT_DIR / 'zero-length-out.txt'
        )

        assert filecmp.cmp(OUT_DIR / 'zero-length-out.txt', EXPECTED_DIR / 'zero-length-expected.txt', shallow=False)
