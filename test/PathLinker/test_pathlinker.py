import pytest
from src.pathlinker import PathLinker

TEST_DIR = 'test/PathLinker/'

class TestPathLinker:
    """
    run PathLinker tests in docker image

    """
    def test_pathlinker_run(self):
        # simple pathlinker run
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_dir = TEST_DIR+'output',
            k=100
        )


