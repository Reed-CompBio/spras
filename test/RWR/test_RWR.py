import sys
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'RWR')))
from spras.rwr import RWR

TEST_DIR = Path('test', 'RWR/')
OUT_FILE = Path(TEST_DIR, 'output', 'rwr-output.txt')


class TestRWR:
    """
    Run the local neighborhood algorithm on the example input files and check the output matches the expected output
    """
    def test_ln(self):
        OUT_FILE.unlink(missing_ok=True)
        RWR.run(network=Path(TEST_DIR, 'input', 'rwr-network.txt'),
                           nodes = Path(TEST_DIR, 'input','rwr-nodes.txt'),
                           alpha = 0.85,
                           output_file= OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected_output', 'rwr-output.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the local neighborhood algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(OSError):
            RWR.run(network=Path(TEST_DIR, 'input', 'missing.txt'),
                            nodes = Path(TEST_DIR, 'input','rwr-nodes.txt'),
                            alpha = 0.85,
                            output_file=OUT_FILE)

    """
    Run the local neighborhood algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        with pytest.raises(ValueError):
            RWR.run(network=Path(TEST_DIR, 'input', 'rwr-bad-network.txt'),
                            nodes = Path(TEST_DIR, 'input','rwr-nodes.txt'),
                            alpha = 0.85,
                            output_file=OUT_FILE)
            