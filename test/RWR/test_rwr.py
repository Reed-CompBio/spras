import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.rwr import RWR

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/RWR/'
OUT_FILE_DEFAULT = TEST_DIR+'output/rwr-edges.txt'


class TestRWR:
    """
    Run PathLinker tests in the Docker image
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
