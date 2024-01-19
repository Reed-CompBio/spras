import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.omicsintegrator2 import OmicsIntegrator2

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/OmicsIntegrator2/'
EDGE_FILE = TEST_DIR+'input/oi2-edges.txt'
PRIZE_FILE = TEST_DIR+'input/oi2-prizes.txt'
OUT_FILE = Path(TEST_DIR, 'output', 'test.tsv')


class TestOmicsIntegrator2:
    """
    Run Omics Integrator 2 in the Docker image
    """
    def test_oi2_required(self):
        # Only include required arguments
        OUT_FILE.unlink(missing_ok=True)
        OmicsIntegrator2.run(edges=EDGE_FILE,
                             prizes=PRIZE_FILE,
                             output_file=OUT_FILE)
        assert OUT_FILE.exists()

    def test_oi2_some_optional(self):
        # Include optional argument
        OUT_FILE.unlink(missing_ok=True)
        OmicsIntegrator2.run(edges=EDGE_FILE,
                             prizes=PRIZE_FILE,
                             output_file=OUT_FILE,
                             g=0)
        assert OUT_FILE.exists()

    def test_oi2_all_optional(self):
        # Include all optional arguments
        OUT_FILE.unlink(missing_ok=True)
        OmicsIntegrator2.run(edges=EDGE_FILE,
                             prizes=PRIZE_FILE,
                             output_file=OUT_FILE,
                             w=5,
                             b=1,
                             g=3,
                             noise=0.1,
                             noisy_edges=0,
                             random_terminals=0,
                             dummy_mode='terminals',
                             seed=2)
        assert OUT_FILE.exists()

    def test_oi2_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No output_file
            OmicsIntegrator2.run(edges=EDGE_FILE,
                                 prizes=PRIZE_FILE)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_oi2_singularity(self):
        # Only include required arguments
        OUT_FILE.unlink(missing_ok=True)
        OmicsIntegrator2.run(edges=EDGE_FILE,
                             prizes=PRIZE_FILE,
                             output_file=OUT_FILE,
                             container_framework="singularity")
        assert OUT_FILE.exists()
