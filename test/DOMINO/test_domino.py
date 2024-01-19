import filecmp
import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.domino import DOMINO, post_domino_id_transform, pre_domino_id_transform

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/DOMINO/'
OUT_FILE_DEFAULT = TEST_DIR+'output/domino-output.txt'
OUT_FILE_OPTIONAL = TEST_DIR+'output/domino-output-thresholds.txt'


class TestDOMINO:
    """
    Run tests for the DOMINO run, parse_output, and id processing functions.
    Intentionally omits a DOMINO run correctness test. The output
    of DOMINO changes between runs without an option to set a seed for
    the algorithm. The variability makes it difficult to compare
    generated output to expected output.
    See https://github.com/Shamir-Lab/DOMINO/issues/5
    """

    def test_domino_required(self):
        # Only include required arguments
        out_path = Path(OUT_FILE_DEFAULT)
        out_path.unlink(missing_ok=True)
        DOMINO.run(
            network=TEST_DIR+'input/domino-network.txt',
            active_genes=TEST_DIR+'input/domino-active-genes.txt',
            output_file=OUT_FILE_DEFAULT)
        # output_file should be empty
        assert out_path.exists()

    def test_domino_optional(self):
        # Include optional arguments
        out_path = Path(OUT_FILE_OPTIONAL)
        out_path.unlink(missing_ok=True)
        DOMINO.run(
            network=TEST_DIR+'input/domino-network.txt',
            active_genes=TEST_DIR+'input/domino-active-genes.txt',
            output_file=OUT_FILE_OPTIONAL,
            slice_threshold=0.4,
            module_threshold=0.06)
        # output_file should be empty
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
            container_framework="singularity")
        assert out_path.exists()

    def test_pre_id_transform(self):
        """
        Test the node ID transformation run before DOMINO executes
        """
        assert pre_domino_id_transform('123') == 'ENSG0123'
        assert pre_domino_id_transform('xyz') == 'ENSG0xyz'

    def test_post_id_transform(self):
        """
        Test the node ID transformation run after DOMINO executes
        """
        assert post_domino_id_transform('ENSG0123') == '123'
        assert post_domino_id_transform('ENSG0xyz') == 'xyz'
        assert post_domino_id_transform('123') == '123'
