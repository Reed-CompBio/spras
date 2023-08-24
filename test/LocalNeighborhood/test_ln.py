import sys
from filecmp import cmp
from pathlib import Path

import pytest

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'LocalNeighborhood')))
from local_neighborhood import local_neighborhood
from src.local_neighborhood import LocalNeighborhood

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
    def test_ln_required(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        LocalNeighborhood.run(
            nodes=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
            network=Path(TEST_DIR, 'input', 'ln-network.txt'),
            output_file=OUT_FILE
        )
        assert out_path.exists()

    def test_ln_optional(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Include optional argument
        LocalNeighborhood.run(
            nodes=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
            network=Path(TEST_DIR, 'input', 'ln-network.txt'),
            output_file=OUT_FILE
        )
        assert out_path.exists()

    def test_ln_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            LocalNeighborhood.run(
                network=Path(TEST_DIR, 'input', 'ln-network.txt'),
                output_file=OUT_FILE
        )
