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
from spras.btb import BowtieBuilder as bowtiebuilder

TEST_DIR = Path('test', 'BowtieBuilder/')
OUT_FILE = Path(TEST_DIR, 'output', 'raw-pathway.txt')


class TestBowtieBuilder:
    """
    Run the bowtiebuilder algorithm on the example input files and check the output matches the expected output
    """
    def test_ln(self):
        print("RUNNING TEST_LN FOR BOWTIEBUILDER")
        OUT_FILE.unlink(missing_ok=True)
        bowtiebuilder.run(source=Path(TEST_DIR, 'input', 'source.txt'),
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'output1.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the bowtiebuilder algorithm with missing arguments
    """
    def test_missing_arguments(self):
        with pytest.raises(ValueError):
            bowtiebuilder.run(
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE)            


    """
    Run the bowtiebuilder algorithm with missing files
    """
    def test_missing_file(self):
        with pytest.raises(ValueError):
            bowtiebuilder.run(source=Path(TEST_DIR, 'input', 'unknown.txt'),
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE)


    """
    Run the bowtiebuilder algorithm with bad input data
    """
    def test_format_error(self):
        with pytest.raises(IndexError):
            bowtiebuilder.run(source=Path(TEST_DIR, 'input', 'source.txt'),
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges_bad.txt'),
                           output_file=OUT_FILE)

