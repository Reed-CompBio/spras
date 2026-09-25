import filecmp
import shutil
from pathlib import Path

import pytest

import spras.config.config as config
from spras.config.container_schema import ContainerFramework, ProcessedContainerSettings
from spras.responsenet import ResponseNet, ResponseNetParams

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'algorithms', 'ResponseNet')
OUT_FILE = TEST_DIR / 'output' / 'rn-output.txt'
EXPECTED_FILE = TEST_DIR / 'expected' / 'rn-expected.txt'
EXPECTED_FILE_OPTIONAL = TEST_DIR / 'expected' / 'rn-expected-optional.txt'


class TestResponseNet:

    def test_responsenet_required(self):
        OUT_FILE.unlink(missing_ok=True)

        ResponseNet.run({"sources": TEST_DIR / 'input' / 'rn-sources.txt',
                         "targets": TEST_DIR / 'input' / 'rn-targets.txt',
                         "edges": TEST_DIR / 'input' / 'rn-edges.txt'},
                        output_file=OUT_FILE)
        assert OUT_FILE.exists()

        assert filecmp.cmp(OUT_FILE, EXPECTED_FILE, shallow=True)

    def test_responsenet_all_optional(self):
        OUT_FILE.unlink(missing_ok=True)
        # Include all optional arguments
        ResponseNet.run({"sources": TEST_DIR / 'input' / 'rn-sources.txt',
                         "targets": TEST_DIR / 'input' / 'rn-targets.txt',
                         "edges": TEST_DIR / 'input' / 'rn-edges.txt'},
                        output_file=OUT_FILE,
                        args=ResponseNetParams(gamma=1))
        assert OUT_FILE.exists()

        assert filecmp.cmp(OUT_FILE, EXPECTED_FILE_OPTIONAL, shallow=True)

    def test_mincostflow_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            ResponseNet.run({"sources": TEST_DIR / 'input' / 'rn-sources.txt',
                             "targets": TEST_DIR / 'input' / 'rn-targets.txt'},
                            output_file=OUT_FILE)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_responsenet_singularity(self):
        OUT_FILE.unlink(missing_ok=True)

        ResponseNet.run({"sources": TEST_DIR / 'input' / 'rn-sources.txt',
                         "targets": TEST_DIR / 'input' / 'rn-targets.txt',
                         "edges": TEST_DIR / 'input' / 'rn-edges.txt'},
                        output_file=OUT_FILE,
                        container_settings=ProcessedContainerSettings(framework=ContainerFramework.singularity))
        assert OUT_FILE.exists()

        assert filecmp.cmp(OUT_FILE, EXPECTED_FILE, shallow=True)
