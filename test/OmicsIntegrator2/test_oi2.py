import pytest

from src.omicsintegrator2 import OmicsIntegrator2

TEST_DIR = 'test/OmicsIntegrator2/'


class TestOmicsIntegrator2:
    """
    Run Omics Integrator 2 in the Docker image
    """
    def test_oi2_required(self):
        # Only include required arguments
        OmicsIntegrator2.run(edges=TEST_DIR+'input/oi2-edges.txt',
                             prizes=TEST_DIR+'input/oi2-prizes.txt',
                             output_file=TEST_DIR+'output/test.tsv')

    def test_oi2_some_optional(self):
        # Include optional argument
        OmicsIntegrator2.run(edges=TEST_DIR+'input/oi2-edges.txt',
                             prizes=TEST_DIR+'input/oi2-prizes.txt',
                             output_file=TEST_DIR+'output/test.tsv',
                             g=0)

    def test_oi2_all_optional(self):
        # Include all optional arguments
        OmicsIntegrator2.run(edges=TEST_DIR+'input/oi2-edges.txt',
                             prizes=TEST_DIR+'input/oi2-prizes.txt',
                             output_file=TEST_DIR+'output/test.tsv',
                             w=5,
                             b=1,
                             g=3,
                             noise=0.1,
                             noisy_edges=0,
                             random_terminals=0,
                             dummy_mode='terminals',
                             seed=2)

    def test_oi2_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No output_file
            OmicsIntegrator2.run(edges=TEST_DIR+'input/oi2-edges.txt',
                                 prizes=TEST_DIR+'input/oi2-prizes.txt')
