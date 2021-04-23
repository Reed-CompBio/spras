import pytest
from src.omicsintegrator2 import OmicsIntegrator2

TEST_DIR = 'test/OmicsIntegrator2/'

class TestOmicsIntegrator2:
    def test_oi2(self):
        """
        Run Omics Integrator 2 in the Docker image using hard-coded arguments.
        """
        # Only include required parameters
        OmicsIntegrator2.run(edge_input=TEST_DIR+'input/oi2-edges.txt',
                             prize_input=TEST_DIR+'input/oi2-prizes.txt',
                             output_dir=TEST_DIR+'output')

        # Include optional parameter
        OmicsIntegrator2.run(edge_input=TEST_DIR+'input/oi2-edges.txt',
                             prize_input=TEST_DIR+'input/oi2-prizes.txt',
                             output_dir=TEST_DIR+'output',
                             g=0)

        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No output_dir
            OmicsIntegrator2.run(edge_input=TEST_DIR+'input/oi2-edges.txt',
                                 prize_input=TEST_DIR+'input/oi2-prizes.txt')
