import filecmp
import shutil
from pathlib import Path

import pytest

from src.domino import DOMINO, post_domino_id_transform, pre_domino_id_transform

TEST_DIR = 'test/DOMINO/'
OUT_FILE_DEFAULT = TEST_DIR+'output/domino-output.txt'
OUT_FILE_OPTIONAL = TEST_DIR+'output/domino-output-thresholds.txt'
OUT_FILE_PARSE = TEST_DIR+'output/domino-parse-output.txt'
OUT_FILE_PARSE_EXP = TEST_DIR+'expected_output/domino-parse-output.txt'


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

    def test_domino_parse_output(self):
        # Input is the concatenated module_0.html and module_1.html file from
        # the DOMINO output of the network dip.sif and the nodes tnfa_active_genes_file.txt
        # from https://github.com/Shamir-Lab/DOMINO/tree/master/examples
        # Confirms the generated output matches the expected output
        out_path = Path(OUT_FILE_PARSE)
        out_path.unlink(missing_ok=True)
        DOMINO.parse_output(
            TEST_DIR+'input/domino-concat-modules.txt',
            OUT_FILE_PARSE)
        assert filecmp.cmp(OUT_FILE_PARSE, OUT_FILE_PARSE_EXP, shallow=False)

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
