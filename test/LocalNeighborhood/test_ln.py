from src.util import compare_files
from src.local_neighborhood import LocalNeighborhood
import pytest
import shutil
from pathlib import Path


TEST_DIR = 'test/LocalNeighborhood/'
OUT_FILE_DEFAULT = TEST_DIR+'output/ln-output.txt'
OUT_FILE_BAD = TEST_DIR+'output/ln-output-bad.txt'

# Write tests for the Local Neighborhood run function here


class TestLocalNeighborhood:
    """
    Run the local neighborhood algorithm on the example input files
    and check the output matches the expected output
    """

    def test_localneighborhood_required(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        LocalNeighborhood.run(
            nodetypes=TEST_DIR+'input/ln-nodes.txt',
            network=TEST_DIR+'input/ln-network.txt',
            output_file=OUT_FILE_DEFAULT
        )
        assert out_path.exists()

        expected_file = TEST_DIR + 'expected_output/ln-output.txt'
        assert compare_files(
            OUT_FILE_DEFAULT, expected_file), 'Output file does not match expected output file'

    def test_localneighborhood_optional(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Include optional argument
        LocalNeighborhood.run(
            nodetypes=TEST_DIR+'input/ln-nodes.txt',
            network=TEST_DIR+'input/ln-bad-network.txt',
            output_file=OUT_FILE_BAD,
        )
        # assert out_path.exists()

    def test_localneighborhood_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            LocalNeighborhood.run(
                network=TEST_DIR + 'input/ln-network.txt',
                output_file=OUT_FILE_DEFAULT)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_localneighborhood_singularity(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        PathLinker.run(
            nodes=TEST_DIR+'input/ln-nodes.txt',
            network=TEST_DIR+'input/ln-network.txt',
            output_file=OUT_FILE,
            singularity=True
        )
        assert out_path.exists()
