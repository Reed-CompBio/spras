import pytest
from src.pathlinker import PathLinker

TEST_DIR = 'test/PathLinker/'


class TestPathLinker:
    """
    Run PathLinker tests in the Docker image
    """
    def test_pathlinker_required(self):
        # Only include required arguments
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=TEST_DIR+'output/pathlinker-ranked-edges.txt',
        )

    def test_pathlinker_optional(self):
        # Include optional argument
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=TEST_DIR+'output/pathlinker-ranked-edges-k100.txt',
            k=100
        )

    def test_pathlinker_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            PathLinker.run(
                network=TEST_DIR + 'input/sample-in-net.txt',
                output_file=TEST_DIR + 'output/pathlinker-ranked-edges-k100.txt',
                k=100)
