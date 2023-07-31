import pytest
import shutil
from pathlib import Path
from src.domino import DOMINO

TEST_DIR = 'test/DOMINO/'
OUT_FILE_DEFAULT = TEST_DIR+'output/domino-output.txt'
OUT_FILE_OPTIONAL = TEST_DIR+'output/domino-output-thresholds.txt'

class TestDOMINO:
    """
    Run test for the DOMINO run function
    """

    def test_domino_required(self):
        # Only include required arguments
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        DOMINO.run(
            network=TEST_DIR+'input/domino-network.txt',
            active_genes=TEST_DIR+'input/domino-active-genes.txt',
            output_file=OUT_FILE_DEFAULT)
        assert out_path.exists()

    def test_domino_optional(self):
        # Include optional argument
        out_path = Path(OUT_FILE_OPTIONAL)
        out_path.unlink(missing_ok=True)
        DOMINO.run(
            network=TEST_DIR+'input/domino-network.txt',
            active_genes=TEST_DIR+'input/domino-active-genes.txt',
            output_file=OUT_FILE_OPTIONAL,
            use_cache=False,
            slices_threshold=0.4,
            module_threshold=0.06)
        assert out_path.exists()

    def test_domino_missing_active_genes(self):
        # Test the expected error is raised when active_genes argument is missing
        with pytest.raises(ValueError):
            # No active_genes
            DOMINO.run(
                network=TEST_DIR+'input/domino-network.txt',
                output_file=OUT_FILE_DEFAULT)

    def test_domino_missing_network(self):
        # Test the expected error is raised when network argument is missing
        with pytest.raises(ValueError):
            # No network
            DOMINO.run(
                active_genes=TEST_DIR+'input/domino-active-genes.txt',
                output_file=OUT_FILE_DEFAULT)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_domino_singularity(self):
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        DOMINO.run(
            network=TEST_DIR+'input/domino-network.txt',
            active_genes=TEST_DIR+'input/domino-active-genes.txt',
            output_file=OUT_FILE_DEFAULT,
            singularity=True)
        assert out_path.exists()
