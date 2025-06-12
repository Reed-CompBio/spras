import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.strwr import ST_RWR

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'ST_RWR')
OUT_FILE = Path(TEST_DIR, 'output', 'strwr-output.txt')
EXPECTED_OUTPUT = Path(TEST_DIR, 'expected_output', 'strwr-output.txt')


class TestSTRWR:
    """
    Run the ST_RWR algorithm on the example input files and check the output matches the expected output
    """
    def test_strwr(self):
        OUT_FILE.unlink(missing_ok=True)
        ST_RWR.run(network=Path(TEST_DIR, 'input', 'strwr-network.txt'),
                   sources=Path(TEST_DIR, 'input', 'strwr-sources.txt'),
                   targets=Path(TEST_DIR, 'input','strwr-targets.txt'),
                   alpha=0.85,
                   output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'

    """
    Run the ST_RWR algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(OSError):
            ST_RWR.run(network=Path(TEST_DIR, 'input', 'missing.txt'),
                       sources=Path(TEST_DIR, 'input', 'strwr-sources.txt'),
                       targets=Path(TEST_DIR, 'input','strwr-targets.txt'),
                       alpha=0.85,
                       output_file=OUT_FILE)

    """
    Run the ST_RWR algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        with pytest.raises(ValueError):
            ST_RWR.run(network=Path(TEST_DIR, 'input', 'strwr-bad-network.txt'),
                       sources=Path(TEST_DIR, 'input', 'strwr-sources.txt'),
                       targets=Path(TEST_DIR, 'input','strwr-targets.txt'),
                       alpha=0.85,
                       output_file=OUT_FILE)
    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_strwr_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        ST_RWR.run(network=Path(TEST_DIR, 'input', 'strwr-network.txt'),
                   sources=Path(TEST_DIR, 'input', 'strwr-sources.txt'),
                   targets=Path(TEST_DIR, 'input','strwr-targets.txt'),
                   alpha=0.85,
                   output_file=OUT_FILE,
                   container_framework="singularity")
        assert OUT_FILE.exists()
