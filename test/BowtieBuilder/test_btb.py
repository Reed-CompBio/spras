import sys
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'BowTieBuilder')))
from spras.btb import BowTieBuilder as BTB

TEST_DIR = Path('test', 'BowTieBuilder/')
OUT_FILE_DEFAULT = Path(TEST_DIR, 'output', 'raw-pathway.txt')


class TestBowTieBuilder:
    """
    Run the BowTieBuilder algorithm on the example input files and check the output matches the expected output
    """
    def test_btb_expected(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(source=Path(TEST_DIR, 'input', 'source.txt'),
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'output1.txt')
        assert cmp(OUT_FILE_DEFAULT, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm with missing arguments
    """
    def test_btb_missing(self):
        with pytest.raises(ValueError):
            # No edges
            BTB.run(
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           sources=Path(TEST_DIR, 'input', 'sources.txt'),
                           output_file=OUT_FILE_DEFAULT)  
        with pytest.raises(ValueError):
            # No source
            BTB.run(
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)
        with pytest.raises(ValueError):
            # No target
            BTB.run(
                           source=Path(TEST_DIR, 'input', 'source.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)


    """
    Run the BowTieBuilder algorithm with missing files
    """
    def test_btb_file(self):
        with pytest.raises(ValueError):
            BTB.run(source=Path(TEST_DIR, 'input', 'unknown.txt'),
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)


    """
    Run the BowTieBuilder algorithm with bad input data
    """
    def test_format_error(self):
        with pytest.raises(IndexError):
            BTB.run(source=Path(TEST_DIR, 'input', 'source.txt'),
                           target=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges_bad.txt'),
                           output_file=OUT_FILE_DEFAULT)