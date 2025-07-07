from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config
from spras.netmix2 import NetMix2

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'NetMix2/')
OUT_FILE = Path(TEST_DIR, 'output', 'ln-output.txt')


class TestNetMix2:
    def test_nm2(self):
        OUT_FILE.unlink(missing_ok=True)
        NetMix2.run(
            network=TEST_DIR / 'input' / 'network-basic.txt',
            scores=TEST_DIR / 'input' / 'scores-basic.txt',
            num_edges=2,
            output_file=OUT_FILE
        )
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = TEST_DIR / 'expected_output' / 'output-basic.txt'
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'
