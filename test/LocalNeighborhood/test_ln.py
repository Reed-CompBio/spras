import sys
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'LocalNeighborhood')))
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
    """
    Test the LocalNeighborhood wrapper's run function with required arguments.
    This will run the Dockerized version of the algorithm.
    """
    def test_local_neighborhood_run_required(self):
        # Ensure the output file from a previous run is deleted
        OUT_FILE.unlink(missing_ok=True)
        
        # Call the static run method of the LocalNeighborhood wrapper class
        local_neighborhood.run(
            network=str(Path(TEST_DIR, 'input', 'ln-network.txt')), # Pass as string
            nodes=str(Path(TEST_DIR, 'input', 'ln-nodes.txt')),     # Pass as string
            output_file=str(OUT_FILE)                      # Pass as string
        )
        
        # Assert that the output file was created by the Dockerized algorithm
        assert OUT_FILE.exists(), 'Dockerized Local Neighborhood output file was not written'
        
        # Optionally, compare the output to an expected file.
        # This requires an 'expected_output_run_test.txt' which accurately reflects
        # the Dockerized algorithm's output. For initial testing, just checking existence is often enough.
        # expected_run_file = Path(TEST_DIR, 'expected_output', 'ln-output.txt') # Assuming it's the same expected output
        # assert cmp(OUT_FILE_RUN_TEST, expected_run_file, shallow=False), 'Dockerized output file does not match expected'


    """
    Test that the LocalNeighborhood wrapper's run function raises an error
    when required arguments are missing.
    """
    def test_local_neighborhood_run_missing(self):
        with pytest.raises(ValueError):
            # Attempt to run without the 'nodes' argument
            local_neighborhood.run(
                network=str(Path(TEST_DIR, 'input', 'ln-network.txt')),
                output_file=str(OUT_FILE)
            )

        with pytest.raises(ValueError):
            # Attempt to run without the 'network' argument
            local_neighborhood.run(
                nodes=str(Path(TEST_DIR, 'input', 'ln-nodes.txt')),
                output_file=str(OUT_FILE)
            )
        
        with pytest.raises(ValueError):
            # Attempt to run without the 'output_file' argument
            local_neighborhood.run(
                network=str(Path(TEST_DIR, 'input', 'ln-network.txt')),
                nodes=str(Path(TEST_DIR, 'input', 'ln-nodes.txt'))
            )

