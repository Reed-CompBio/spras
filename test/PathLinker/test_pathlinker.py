from src.pathlinker import PathLinker

TEST_DIR = 'test/PathLinker/'


class TestPathLinker:
    """
    Run PathLinker tests in the Docker image
    """
    def test_pathlinker_run(self):
        # simple PathLinker run
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=TEST_DIR+'output/pathlinker-ranked-edges.txt',
            k=100
        )
