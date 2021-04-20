from src.omicsintegrator1 import OmicsIntegrator1

TEST_DIR = 'test/OmicsIntegrator1/'


class TestOmicsIntegrator1:
    def test_oi1(self):
        """
        Run Omics Integrator 1 in the Docker image using hard-coded arguments.
        """
        # Only include required parameters
        OmicsIntegrator1.run(edge_input=TEST_DIR+'input/oi1-edges.txt',
                             prize_input=TEST_DIR+'input/oi1-prizes.txt',
                             output_dir=TEST_DIR+'output')

        # Include optional parameter
        OmicsIntegrator1.run(edge_input=TEST_DIR+'input/oi1-edges.txt',
                             prize_input=TEST_DIR+'input/oi1-prizes.txt',
                             output_dir=TEST_DIR+'output',
                             out_label='oi1')
