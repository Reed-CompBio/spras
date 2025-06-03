import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.edgelinker import EdgeLinker

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'EdgeLinker')
OUT_FILE = TEST_DIR / 'output' / 'pathlinker-ranked-edges.txt'


class TestEdgeLinker:
    """
    Run EdgeLinker tests in the Docker image
    """
    def test_edgelinker_required(self):
        OUT_FILE.unlink(missing_ok=True)
        # Only include required arguments
        EdgeLinker.run(
            network=TEST_DIR / 'input' / 'network.txt',
            sources=TEST_DIR / 'input' / 'sources.txt',
            targets=TEST_DIR / 'input' / 'targets.txt',
            output_file=OUT_FILE
        )
        assert OUT_FILE.exists()

    def test_edgelinker_optional(self):
        OUT_FILE.unlink(missing_ok=True)
        # Include optional argument
        EdgeLinker.run(
            network=TEST_DIR / 'input' / 'network.txt',
            sources=TEST_DIR / 'input' / 'sources.txt',
            targets=TEST_DIR / 'input' / 'targets.txt',
            output_file=OUT_FILE,
            k=150
        )
        assert OUT_FILE.exists()

    def test_edgelinker_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No nodetypes
            EdgeLinker.run(
                network=TEST_DIR / 'input' / 'network.txt',
                sources=TEST_DIR / 'input' / 'sources.txt',
                output_file=OUT_FILE,
                k=100)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_edgelinker_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        EdgeLinker.run(
            network=TEST_DIR / 'input' / 'network.txt',
            sources=TEST_DIR / 'input' / 'sources.txt',
            targets=TEST_DIR / 'input' / 'targets.txt',
            output_file=OUT_FILE,
            container_framework="singularity")
        assert OUT_FILE.exists()
