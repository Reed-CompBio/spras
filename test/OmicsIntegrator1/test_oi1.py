import pytest
from src.omicsintegrator1 import OmicsIntegrator1

TEST_DIR = 'test/OmicsIntegrator1/'


class TestOmicsIntegrator1:
    """
    Run Omics Integrator 1 in the Docker image
    """
    def test_oi1_required(self):
        # Only include required parameters
        OmicsIntegrator1.run(edge_input=TEST_DIR+'input/oi1-edges.txt',
                             prize_input=TEST_DIR+'input/oi1-prizes.txt',
                             output_dir=TEST_DIR+'output')

    def test_oi1_some_optional(self):
        # Include optional parameter
        OmicsIntegrator1.run(edge_input=TEST_DIR+'input/oi1-edges.txt',
                             prize_input=TEST_DIR+'input/oi1-prizes.txt',
                             output_dir=TEST_DIR+'output',
                             out_label='oi1')

    def test_oi1_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edge_input
            OmicsIntegrator1.run(prize_input=TEST_DIR + 'input/oi1-prizes.txt',
                                 output_dir=TEST_DIR + 'output')
