import sys
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

from local_neighborhood import local_neighborhood

TEST_DIR = Path('test', 'LocalNeighborhood/')
OUT_FILE = Path(TEST_DIR, 'output', 'ln-output.txt')


class TestLocalNeighborhood:
    """
    Run the local neighborhood algorithm on the example input files and check the output matches the expected output
    """
    def test_ln(self):
        OUT_FILE.unlink(missing_ok=True)
        local_neighborhood(network_file=Path(TEST_DIR, 'input', 'ln-network.txt'),
                           nodes_file=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
                           output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected_output', 'ln-output.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the local neighborhood algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(OSError):
            local_neighborhood(network_file=Path(TEST_DIR, 'input', 'missing.txt'),
                               nodes_file=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
                               output_file=OUT_FILE)

    """
    Run the local neighborhood algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        with pytest.raises(ValueError):
            local_neighborhood(network_file=Path(TEST_DIR, 'input', 'ln-bad-network.txt'),
                               nodes_file=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
                               output_file=OUT_FILE)

    # Write tests for the Local Neighborhood run function here
def test_localneighborhood_run():
    """
    Run Localneighborhood with the run function and check the output matches the expected output
    """
    # Remove the output file if it exists
    out_path = Path(OUT_FILE)
    out_path.unlink(missing_ok=True)
    # Run the run function in LocalNeighborhood
    local_neighborhood.run(
        nodes=TEST_DIR + 'input/ln-nodes.txt',
        network=TEST_DIR + 'input/ln-network.txt',
        output_file=OUT_FILE
    )
    assert out_path.exists()
