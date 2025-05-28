import filecmp
from pathlib import Path

import spras.config as config
from spras.robust import ROBUST

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'ROBUST')
OUT_FILE = TEST_DIR / 'output' / 'edges.txt'


class TestROBUST:
    def test_robust_required(self):
        OUT_FILE.unlink(missing_ok=True)
        ROBUST.run(network=TEST_DIR / 'input' / 'robust-network.txt',
                   scores=TEST_DIR / 'input' / 'robust-scores.txt',
                   seeds=TEST_DIR / 'input' / 'robust-seeds.txt',
                   output_file=OUT_FILE)
        assert OUT_FILE.exists()

        assert "B" in (TEST_DIR / 'expected' / 'robust-edges-required.txt').read_text()
