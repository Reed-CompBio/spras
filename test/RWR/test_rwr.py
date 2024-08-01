import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.rwr import RWR

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/RWR/'
OUT_FILE_DEFAULT = TEST_DIR+'output/rwr-edges.txt'
OUT_FILE_OPTIONAL = TEST_DIR+'output/rwr-edges-optional.txt'


class TestRWR:
    """
    Run RWR tests in the Docker image
    """
    def test_rwr(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        RWR.run(
            edges=TEST_DIR+'input/edges.txt',
            prizes=TEST_DIR+'input/prizes.txt',
            output_file=OUT_FILE_DEFAULT
        )
        assert out_path.exists()

    def test_rwr_optional(self):
        out_path = Path(OUT_FILE_OPTIONAL)
        out_path.unlink(missing_ok=True)
        # Include optional argument - single_source, df, w, f, threshold,
        RWR.run(
            edges=TEST_DIR+'input/edges.txt',
            prizes=TEST_DIR+'input/prizes.txt',
            output_file=OUT_FILE_OPTIONAL,
            single_source=1,
            df=0.85,
            w=0.00,
            f='min',
            threshold=0.0001
        )
        assert out_path.exists()

    def test_rwr_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            RWR.run(
                edges=TEST_DIR + 'input/edges.txt',
                output_file=OUT_FILE_OPTIONAL,
                single_source=1,
                df=0.85)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_rwr_singularity(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        RWR.run(
            edges=TEST_DIR+'input/edges.txt',
            prizes=TEST_DIR+'input/prizes.txt',
            output_file=OUT_FILE_DEFAULT,
            container_framework="singularity")
        assert out_path.exists()
