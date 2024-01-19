import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.pathlinker import PathLinker

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/PathLinker/'
OUT_FILE_DEFAULT = TEST_DIR+'output/pathlinker-ranked-edges.txt'
OUT_FILE_100 = TEST_DIR+'output/pathlinker-ranked-edges-k100.txt'


class TestPathLinker:
    """
    Run PathLinker tests in the Docker image
    """
    def test_pathlinker_required(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_FILE_DEFAULT
        )
        assert out_path.exists()

    def test_pathlinker_optional(self):
        out_path = Path(OUT_FILE_100)
        out_path.unlink(missing_ok=True)
        # Include optional argument
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_FILE_100,
            k=100
        )
        assert out_path.exists()

    def test_pathlinker_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            PathLinker.run(
                network=TEST_DIR + 'input/sample-in-net.txt',
                output_file=OUT_FILE_100,
                k=100)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_pathlinker_singularity(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        PathLinker.run(
            nodetypes=TEST_DIR+'input/sample-in-nodetypes.txt',
            network=TEST_DIR+'input/sample-in-net.txt',
            output_file=OUT_FILE_DEFAULT,
            container_framework="singularity")
        assert out_path.exists()
