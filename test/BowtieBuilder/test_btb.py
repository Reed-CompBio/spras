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
OUT_FILE = Path(TEST_DIR, 'output', 'output.txt')
OUT_FILE_DEFAULT = Path(TEST_DIR, 'output', 'raw-pathway.txt')
BTB_OUT_FILE = Path(TEST_DIR, 'output', 'btb-output.txt')
DISJOINT_OUT_FILE = Path(TEST_DIR, 'output', 'disjoint-output.txt')
DISJOINT2_OUT_FILE = Path(TEST_DIR, 'output', 'disjoint2-output.txt')
SOURCE_TO_SOURCE_OUT_FILE = Path(TEST_DIR, 'output', 'source-to-source-output.txt')
SOURCE_TO_SOURCE2_OUT_FILE = Path(TEST_DIR, 'output', 'source-to-source2-output.txt')
SOURCE_TO_SOURCE_DISJOINT_OUT_FILE = Path(TEST_DIR, 'output', 'source-to-source-disjoint-output.txt')
BIDIRECTIONAL_OUT_FILE = Path(TEST_DIR, 'output', 'bidirectional-output.txt')
TARGET_TO_SOURCE_OUT_FILE = Path(TEST_DIR, 'output', 'target-to-source-output.txt')
LOOP_OUT_FILE = Path(TEST_DIR, 'output', 'loop-output.txt')
WEIGHTED_OUT_FILE = Path(TEST_DIR, 'output', 'weighted-output.txt')
NO_WEIGHT_OUT_FILE = Path(TEST_DIR, 'output', 'no-weight-output.txt')
WEIGHT_ONE_OUT_FILE = Path(TEST_DIR, 'output', 'weight-one-output.txt')


class TestBowTieBuilder:
    """
    Run the BowTieBuilder algorithm with missing arguments
    """
    def test_btb_missing(self):
        with pytest.raises(ValueError):
            # No edges
            BTB.run(
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           sources=Path(TEST_DIR, 'input', 'sources.txt'),
                           output_file=OUT_FILE_DEFAULT)  
        with pytest.raises(ValueError):
            # No source
            BTB.run(
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)
        with pytest.raises(ValueError):
            # No target
            BTB.run(
                           sources=Path(TEST_DIR, 'input', 'source.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)


    """
    Run the BowTieBuilder algorithm with missing files
    """
    def test_btb_file(self):
        with pytest.raises(ValueError):
            BTB.run(sources=Path(TEST_DIR, 'input', 'unknown.txt'),
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges.txt'),
                           output_file=OUT_FILE_DEFAULT)
            
    """
    Run the BowTieBuilder algorithm on the example input files and check the output matches the expected output
    """
    def test_btb(self):
            OUT_FILE_DEFAULT.unlink(missing_ok=True)
            BTB.run(edges=Path(TEST_DIR, 'input', 'btb-edges.txt'),
                            sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                            targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                            output_file=OUT_FILE_DEFAULT)
            assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
            expected_file = Path(TEST_DIR, 'expected', 'btb-output.txt')

            # Read the content of the output files and expected file into sets
            with open(OUT_FILE_DEFAULT, 'r') as output_file:
                output_content = set(output_file.read().splitlines())
            with open(expected_file, 'r') as expected_output_file:
                expected_content = set(expected_output_file.read().splitlines())

            # Check if the sets are equal, regardless of the order of lines
            assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the example disjoint input files and check the output matches the expected output
    """
    def test_disjoint(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'disjoint-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'disjoint-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'disjoint-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'disjoint-output.txt')

        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the example disjoint2 input files and check the output matches the expected output
    """
    def test_disjoint2(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'disjoint2-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'disjoint-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'disjoint-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'disjoint-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(ValueError):
            with pytest.raises(OSError):
                BTB.run(edges=Path(TEST_DIR, 'input', 'missing.txt'),
                            sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                            targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                            output_file=OUT_FILE_DEFAULT)
            

    """
    Run the BowTieBuilder algorithm on the example source to source input files and check the output matches the expected output
    """
    def test_source_to_source(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'source-to-source-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'source-to-source-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the example source to source input files and check the output matches the expected output
    """
    def test_source_to_source2(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'source-to-source2-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'source-to-source2-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on two separate source to target paths connected by sources and check the output matches the expected output
    """

    def test_source_to_source_disjoint(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'source-to-source-disjoint-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'source-to-source-disjoint-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the example bidirectional input files and check the output matches the expected output
    """

    def test_bidirectional(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'bidirectional-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'bidirectional-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the example target to source input files and check the output matches the expected output
    """

    def test_target_to_source(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'target-to-source-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'empty-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the example loop network files and check the output matches the expected output
    """

    def test_loop(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'loop-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'loop-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    """
    Run the BowTieBuilder algorithm on the weighted input files and check the output matches the expected output
    """

    def test_weighted(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'weighted-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'weighted-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'

    def test_weight_one(self):
        OUT_FILE_DEFAULT.unlink(missing_ok=True)
        BTB.run(edges=Path(TEST_DIR, 'input', 'weight-one-edges.txt'),
                           sources=Path(TEST_DIR, 'input', 'btb-sources.txt'),
                           targets=Path(TEST_DIR, 'input', 'btb-targets.txt'),
                           output_file=OUT_FILE_DEFAULT)
        assert OUT_FILE_DEFAULT.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected', 'weighted-output.txt')
        
        # Read the content of the output files and expected file into sets
        with open(OUT_FILE_DEFAULT, 'r') as output_file:
            output_content = set(output_file.read().splitlines())
        with open(expected_file, 'r') as expected_output_file:
            expected_content = set(expected_output_file.read().splitlines())

        # Check if the sets are equal, regardless of the order of lines
        assert output_content == expected_content, 'Output file does not match expected output file'
    
        """
    Run the BowTieBuilder algorithm with bad input data
    """
    def test_format_error(self):
        with pytest.raises(IndexError):
            BTB.run(sources=Path(TEST_DIR, 'input', 'source.txt'),
                           targets=Path(TEST_DIR, 'input', 'target.txt'),
                           edges=Path(TEST_DIR, 'input', 'edges_bad.txt'),
                           output_file=OUT_FILE_DEFAULT)