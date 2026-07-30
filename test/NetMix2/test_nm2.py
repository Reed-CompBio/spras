import shutil
from pathlib import Path

import pytest

import spras.config.config as config
from spras.netmix2 import NetMix2, NetMix2Params
from spras.secrets import gurobi

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'NetMix2/')
OUT_FILE = Path(TEST_DIR, 'output', 'nm2-output.txt')


class TestNetMix2:
    #testing the existence of the license for gurobi, which is required for NetMix2 to run
    def test_gurobi_license(self):
        assert gurobi() is not None, "Gurobi license not found."

    def test_nm2_required(self):
        OUT_FILE.unlink(missing_ok=True)
        # inputs must be a dict, not keyword args (consistent with other SPRAS wrappers)
        # num_edges=1 required because test network has far fewer than 175000 edges
        # container_settings loaded from global config (set by init_from_file above)
        NetMix2.run(
            {"network": TEST_DIR / 'input' / 'network-basic.txt',
             "scores": TEST_DIR / 'input' / 'scores-basic.txt'},
            output_file=OUT_FILE,
            args=NetMix2Params(num_edges=1),
            container_settings=config.config.container_settings
        )

        assert OUT_FILE.exists(), 'Output file was not written'

    def test_nm2_optional(self):
        OUT_FILE.unlink(missing_ok=True)
        # inputs must be a dict; optional params passed via NetMix2Params
        # container_settings loaded from global config (set by init_from_file above)
        NetMix2.run(
            {"network": TEST_DIR / 'input' / 'network-basic.txt',
             "scores": TEST_DIR / 'input' / 'scores-basic.txt'},
            output_file=OUT_FILE,
            args=NetMix2Params(num_edges=1, delta=1, density=5),
            container_settings=config.config.container_settings
        )
        assert OUT_FILE.exists(), 'Output file was not written'

    def test_nm2_missing(self):
        # scores is missing — should raise ValueError
        with pytest.raises(ValueError):
            NetMix2.run(
                {"network": TEST_DIR / 'input' / 'network-basic.txt'},
                output_file=OUT_FILE,
                args=NetMix2Params(),
                container_settings=config.config.container_settings
            )

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_nm2_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        NetMix2.run(
            {"network": TEST_DIR / 'input' / 'network-basic.txt',
             "scores": TEST_DIR / 'input' / 'scores-basic.txt'},
            output_file=OUT_FILE,
            # There are notably less than 175,000 edges in our test network,
            # so this is required.
            args=NetMix2Params(num_edges=1),
            container_settings=config.config.container_settings
        )
        assert OUT_FILE.exists(), 'Output file was not written'
