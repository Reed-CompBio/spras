import pytest
import docker
from src.allpairs import AllPairs

TEST_DIR = 'test/AllPairs/'
OUT_FILE = TEST_DIR+'out.txt'

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

    def test_pathlinker_missing(self):
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
