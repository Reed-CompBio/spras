import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.robust import ROBUST

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'ROBUST')
OUT_FILE = TEST_DIR / 'output' / 'edges.txt'


class TestROBUST:
    def test_robust_required(self):
        OUT_FILE.unlink(missing_ok=True)
        ROBUST.run(network=TEST_DIR / 'input' / 'robust-network.txt',
                   seeds=TEST_DIR / 'input' / 'robust-seeds.txt',
                   output_file=OUT_FILE)
        assert OUT_FILE.exists()

        assert "A" in OUT_FILE.read_text()
        assert "Z" in OUT_FILE.read_text()
    
    def test_robust_scores(self):
        OUT_FILE.unlink(missing_ok=True)
        ROBUST.run(network=TEST_DIR / 'input' / 'robust-network.txt',
                   scores=TEST_DIR / 'input' / 'robust-scores.txt',
                   seeds=TEST_DIR / 'input' / 'robust-seeds.txt',
                   output_file=OUT_FILE)
        assert OUT_FILE.exists()

        # Unfortunately, despite repeated tests indicating that ROBUST is more likely
        # to traverse the non-penalized edges, we still can't guarantee that ROBUST won't explore them.
        assert "A" in OUT_FILE.read_text()
        assert "Z" in OUT_FILE.read_text()

    def test_robust_optional(self):
        OUT_FILE.unlink(missing_ok=True)
        # specify all optional parameters
        ROBUST.run(network=TEST_DIR / 'input' / 'robust-network.txt',
                   scores=TEST_DIR / 'input' / 'robust-scores.txt',
                   seeds=TEST_DIR / 'input' / 'robust-seeds.txt',
                   alpha=0.5,
                   beta=0.25,
                   n=40,
                   tau=0.2,
                   gamma=0.5,
                   output_file=OUT_FILE)
        assert OUT_FILE.exists()

    def test_robust_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No seeds
            ROBUST.run(network=TEST_DIR / 'input' / 'robust-network.txt',
                   output_file=OUT_FILE)


    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_robust_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        ROBUST.run(network=TEST_DIR / 'input' / 'robust-network.txt',
                   seeds=TEST_DIR / 'input' / 'robust-seeds.txt',
                   container_framework='singularity',
                   output_file=OUT_FILE)
        assert OUT_FILE.exists()
