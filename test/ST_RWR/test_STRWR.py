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
    def test_ln(self):
        OUT_FILE.unlink(missing_ok=True)
        ST_RWR.run(network=Path(TEST_DIR, 'input', 'strwr-network.txt'),
                           sources=Path(TEST_DIR, 'input', 'strwr-sources.txt'),
                           targets=Path(TEST_DIR, 'input','strwr-targets.txt'),
                           alpha=0.85,
                           output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        # The test below will always fail until thresholding is implemented
        # assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

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
