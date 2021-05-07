import pytest
from pathlib import Path
from src.omicsintegrator1 import OmicsIntegrator1, write_conf

TEST_DIR = 'test/OmicsIntegrator1/'


class TestOmicsIntegrator1:
    """
    Run Omics Integrator 1 in the Docker image
    """
    def test_oi1_required(self):
        # Only include required arguments
        OmicsIntegrator1.run(edges=TEST_DIR+'input/oi1-edges.txt',
                             prizes=TEST_DIR+'input/oi1-prizes.txt',
                             outpath=TEST_DIR + 'output',
                             w=5,
                             b=1,
                             d=10)

    def test_oi1_some_optional(self):
        # Include optional argument
        OmicsIntegrator1.run(edges=TEST_DIR+'input/oi1-edges.txt',
                             prizes=TEST_DIR+'input/oi1-prizes.txt',
                             outpath=TEST_DIR + 'output',
                             w=5,
                             b=1,
                             d=10,
                             outlabel='oi1')

    def test_oi1_all_optional(self):
        # Include all optional arguments
        OmicsIntegrator1.run(edges=TEST_DIR+'input/oi1-edges.txt',
                             prizes=TEST_DIR+'input/oi1-prizes.txt',
                             dummy_mode='terminals',
                             mu_squared=True,
                             exclude_terms=True,
                             outpath=TEST_DIR + 'output',
                             outlabel='oi1',
                             noisy_edges=0,
                             shuffled_prizes=0,
                             random_terminals=0,
                             seed=1,
                             w=5,
                             b=1,
                             d=10,
                             mu=0,
                             noise=0.333,
                             g=0.001,
                             r=0)

    def test_oi1_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edges
            OmicsIntegrator1.run(prizes=TEST_DIR + 'input/oi1-prizes.txt',
                                 outpath=TEST_DIR + 'output',
                                 w=5,
                                 b=1,
                                 d=10)
        with pytest.raises(ValueError):
            # No w
            write_conf(Path('.'),
                       b=1,
                       d=10)
