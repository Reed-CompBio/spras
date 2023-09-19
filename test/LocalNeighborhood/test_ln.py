import shutil
import sys
from filecmp import cmp
from pathlib import Path

import pytest

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'LocalNeighborhood')))

from src.local_neighborhood import LocalNeighborhood

TEST_DIR = 'test/LocalNeighborhood/'
OUT_FILE = TEST_DIR+'output/ln-output.txt'


class TestLocalNeighborhood:
    """
    Run the local neighborhood algorithm on the example input files and check the output matches the expected output
    """
    def test_ln(self):
        out_path=Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        LocalNeighborhood.run(
                           nodes=TEST_DIR+'input/ln-nodes.txt',
                           network=TEST_DIR+'input/ln-network.txt',
                           output_file=OUT_FILE
                           )
        assert out_path.exists(), 'Output file was not written'
        expected_file = TEST_DIR+'expected_output/ln-output.txt'
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the local neighborhood algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(OSError):
            LocalNeighborhood.run(
                               nodes=TEST_DIR+'input/ln-nodes.txt',
                               network=TEST_DIR+'input/missing.txt',
                               output_file=OUT_FILE
                               )

    """
    Run the local neighborhood algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        with pytest.raises(ValueError):
            LocalNeighborhood.run(
                               network=TEST_DIR+'input/ln-bad-network.txt',
                               output_file=OUT_FILE
            )

    # Write tests for the Local Neighborhood run function here

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_ln_singularity(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        LocalNeighborhood.run(
            nodes=TEST_DIR+'input/ln-nodes.txt',
            network=TEST_DIR+'input/ln-network.txt',
            output_file=OUT_FILE
        )
        assert out_path.exists()
