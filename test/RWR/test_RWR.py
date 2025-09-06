import shutil
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config.config as config
from spras.rwr import RWR, RWRParams

config.init_from_file("config/config.yaml")

TEST_DIR = Path('test', 'RWR/')
OUT_FILE = Path(TEST_DIR, 'output', 'rwr-output.txt')


class TestRWR:
    """
    Run the RWR algorithm on the example input files and check the output matches the expected output
    """
    def test_rwr(self):
        OUT_FILE.unlink(missing_ok=True)
        RWR.run({"network": Path(TEST_DIR, 'input', 'rwr-network.txt'),
                 "nodes": Path(TEST_DIR, 'input','rwr-nodes.txt')},
                args=RWRParams(alpha=0.85, threshold=200),
                output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected_output', 'rwr-output.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the RWR algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(OSError):
            RWR.run({"network": Path(TEST_DIR, 'input', 'missing.txt'),
                     "nodes": Path(TEST_DIR, 'input','rwr-nodes.txt')},
                    args=RWRParams(alpha=0.85, threshold=200),
                    output_file=OUT_FILE)

    """
    Run the RWR algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        with pytest.raises(ValueError):
            RWR.run({"network": Path(TEST_DIR, 'input', 'rwr-bad-network.txt'),
                     "nodes": Path(TEST_DIR, 'input','rwr-nodes.txt')},
                    args=RWRParams(alpha=0.85, threshold=200),
                    output_file=OUT_FILE)

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_rwr_singularity(self):
        OUT_FILE.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        RWR.run({"network": Path(TEST_DIR, 'input', 'rwr-network.txt'),
                 "nodes": Path(TEST_DIR, 'input','rwr-nodes.txt')},
                args=RWRParams(alpha=0.85, threshold=200),
                output_file=OUT_FILE,
                container_framework="singularity")
        assert OUT_FILE.exists()
