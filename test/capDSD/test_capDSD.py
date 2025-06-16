import filecmp
import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.capDSD import CapDSD

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'capDSD')
IN_DIR = TEST_DIR / 'input'
OUT_DIR = TEST_DIR / 'output'
EXPECTED_DIR = TEST_DIR / 'expected'

INPUT_PPI = IN_DIR / 'capdsd-ppi.txt'
INPUT_PPIP = IN_DIR / 'capdsd-ppip.txt'

OUT_FILE = OUT_DIR / 'output.txt'
EXPECTED_FILE = EXPECTED_DIR / 'capdsd-matrix-expected.txt'

class TestCapDSD:
    """
    Run capDSD tests in the Docker image
    """
    def test_capdsd_required(self):
        OUT_FILE.unlink(missing_ok=True)
        # Only include required arguments
        CapDSD.run(
            ppi=INPUT_PPI,
            ppip=INPUT_PPIP,
            output_file=OUT_FILE
        )
        assert OUT_FILE.exists()

        assert filecmp.cmp(OUT_FILE, EXPECTED_FILE)

    def test_capdsd_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No PPI
            CapDSD.run(
                ppip=INPUT_PPIP,
                output_file=OUT_FILE
            )

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_capdsd_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        CapDSD.run(
            ppi=INPUT_PPI,
            ppip=INPUT_PPIP,
            output_file=OUT_FILE,
            container_framework="singularity")
        assert OUT_FILE.exists()

        assert filecmp.cmp(OUT_FILE, EXPECTED_FILE)
