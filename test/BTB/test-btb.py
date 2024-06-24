import sys
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'BowtieBuilder')))
from spras.btb import BowtieBuilder

TEST_DIR = Path('test', 'bowtiebuilder/')
OUT_FILE = Path(TEST_DIR, 'output', 'output1.txt')


class TestBowtieBuilder:
    """
    Run the bowtiebuilder algorithm on the example input files and check the output matches the expected output
    """
    def test_ln(self):
        print("RUNNING TEST_LN FOR BOWTIEBUILDER")
        OUT_FILE.unlink(missing_ok=True)
        BowtieBuilder(sources=Path(TEST_DIR, 'input', 'source.txt'),
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'output1.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the bowtiebuilder algorithm with a missing input file
    """
    def test_missing_file(self):
        print("RUNNING TEST_MISSING_FILE FOR BOWTIEBUILDER")
        with pytest.raises(OSError):
            BowtieBuilder(sources=Path(TEST_DIR, 'input', 'missing.txt'),
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE)

    """
    Run the local neighborhood algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        print("RUNNING TEST_FORMAT_ERROR FOR BOWTIEBUILDER")
        with pytest.raises(ValueError):
            BowtieBuilder( sources=Path(TEST_DIR, 'input', 'source.txt'),
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges_bad.txt'),
                           output_file=OUT_FILE )
