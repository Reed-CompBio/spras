import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.diamond import DIAMOnD

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'DIAMOnD')
OUT_FILE = TEST_DIR / 'output' / 'diamond-output.txt'


class TestDIAMOnD:
    # `medium` is the "medium-sized" DIAMOnD-provided dataset
    def test_diamond_medium(self):
        OUT_FILE.unlink(missing_ok=True)
        DIAMOnD.run(
            network=TEST_DIR / 'input' / 'diamond-medium-network.txt',
            seeds=TEST_DIR / 'input' / 'diamond-medium-seeds.txt',
            output_file=OUT_FILE)
        assert OUT_FILE.exists()

    def test_diamond_required(self):
        OUT_FILE.unlink(missing_ok=True)
        DIAMOnD.run(
            network=TEST_DIR / 'input' / 'diamond-network.txt',
            seeds=TEST_DIR / 'input' / 'diamond-seeds.txt',
            output_file=OUT_FILE,
            n=2)
        assert OUT_FILE.exists()

    def test_diamond_optional(self):
        OUT_FILE.unlink(missing_ok=True)
        DIAMOnD.run(
            network=TEST_DIR / 'input' / 'diamond-network.txt',
            seeds=TEST_DIR / 'input' / 'diamond-seeds.txt',
            alpha=0,
            output_file=OUT_FILE,
            n=2)
        assert OUT_FILE.exists()

    def test_DIAMOnD_missing_seeds(self):
        with pytest.raises(ValueError):
            # No seeds
            DIAMOnD.run(
                network=TEST_DIR / 'input' / 'diamond-network.txt',
                output_file=OUT_FILE)

    def test_domino_missing_network(self):
        # Test the expected error is raised when network argument is missing
        with pytest.raises(ValueError):
            # No seeds
            DIAMOnD.run(
                seeds=TEST_DIR / 'input' / 'diamond-seeds.txt',
                output_file=OUT_FILE)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_domino_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        DIAMOnD.run(
            network=TEST_DIR / 'input' / 'diamond-network.txt',
            seeds=TEST_DIR / 'input' / 'diamond-seeds.txt',
            output_file=OUT_FILE,
            n=2)
        assert OUT_FILE.exists()
