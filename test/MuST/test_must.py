import shutil
from pathlib import Path

import pytest

import spras.config.config as config
from spras.config.container_schema import ContainerFramework, ProcessedContainerSettings
from spras.must import MuST, MuSTParams

config.init_from_file("config/config.yaml")

INPUT_DIR = Path('test', 'MuST', 'input')
OUTPUT_DIR = Path('test', 'MuST', 'output')
SIMPLE_OUT_FILE = OUTPUT_DIR / 'simple-out.txt'

class TestMuST:
    def test_must_required(self):
        SIMPLE_OUT_FILE.unlink(missing_ok=True)

        MuST.run({"seeds": INPUT_DIR / 'simple-seeds.txt',
                  "network": INPUT_DIR / 'simple-network.txt'},
                 output_file=SIMPLE_OUT_FILE)

        assert SIMPLE_OUT_FILE.exists()

    def test_must_optional(self):
        SIMPLE_OUT_FILE.unlink(missing_ok=True)

        MuST.run({"seeds": INPUT_DIR / 'simple-seeds.txt',
                  "network": INPUT_DIR / 'simple-network.txt'},
                  args=MuSTParams(
                      no_largest_cc=True,
                      max_iterations=12,
                      hub_penalty=0.5),
                 output_file=SIMPLE_OUT_FILE)

        assert SIMPLE_OUT_FILE.exists()

    def test_must_missing(self):
        with pytest.raises(ValueError):
            # No network
            MuST.run({"seeds": INPUT_DIR / 'simple-seeds.txt'},
                     output_file=OUTPUT_DIR / 'simple-text.txt')

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_must_singularity(self):
        SIMPLE_OUT_FILE.unlink(missing_ok=True)

        # Only include required arguments and run with Singularity
        MuST.run({"seeds": INPUT_DIR / 'simple-seeds.txt',
                  "network": INPUT_DIR / 'simple-network.txt'},
                  output_file=SIMPLE_OUT_FILE,
                 container_settings=ProcessedContainerSettings(framework=ContainerFramework.singularity))

        assert SIMPLE_OUT_FILE.exists()
