import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.netmix2 import NetMix2

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'NetMix2/')
OUT_FILE = Path(TEST_DIR, 'output', 'nm2-output.txt')


class TestNetMix2:
    def test_nm2_required(self):
        OUT_FILE.unlink(missing_ok=True)
        NetMix2.run(
            network=TEST_DIR / 'input' / 'network-basic.txt',
            scores=TEST_DIR / 'input' / 'scores-basic.txt',
            output_file=OUT_FILE,
            # There are notably less than 175,000 edges in our test network,
            # so this is required.
            num_edges=1
        )
        assert OUT_FILE.exists(), 'Output file was not written'

    def test_nm2_optional(self):
        OUT_FILE.unlink(missing_ok=True)
        NetMix2.run(
            network=TEST_DIR / 'input' / 'network-basic.txt',
            scores=TEST_DIR / 'input' / 'scores-basic.txt',
            num_edges=1,
            delta=1,
            density=5,
            output_file=OUT_FILE
        )
        assert OUT_FILE.exists(), 'Output file was not written'

    def test_nm2_missing(self):
        with pytest.raises(ValueError):
            NetMix2.run(
            network=TEST_DIR / 'input' / 'network-basic.txt',
            output_file=OUT_FILE,
        )

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_nm2_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        NetMix2.run(
            network=TEST_DIR / 'input' / 'network-basic.txt',
            scores=TEST_DIR / 'input' / 'scores-basic.txt',
            output_file=OUT_FILE,
            # There are notably less than 175,000 edges in our test network,
            # so this is required.
            num_edges=1
        )
        assert OUT_FILE.exists(), 'Output file was not written'
