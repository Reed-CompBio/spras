import sys
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

# TODO consider refactoring to simplify the import
# Modify the path because of the - in the directory
SPRAS_ROOT = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(Path(SPRAS_ROOT, 'docker-wrappers', 'LocalNeighborhood')))
from local_neighborhood import local_neighborhood 
#from local_neighborhood import LocalNeighborhood as LocalNeighborhoodWrapper

TEST_DIR = Path('test', 'LocalNeighborhood/')
OUT_FILE = Path(TEST_DIR, 'output', 'ln-output.txt')


class TestLocalNeighborhood:
    """
    Run the local neighborhood algorithm on the example input files and check the output matches the expected output
    """
    def test_ln(self):
        OUT_FILE.unlink(missing_ok=True)
        local_neighborhood(network_file=Path(TEST_DIR, 'input', 'ln-network.txt'),
                           nodes_file=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
                           output_file=OUT_FILE)
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected_output', 'ln-output.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'

    """
    Run the local neighborhood algorithm with a missing input file
    """
    def test_missing_file(self):
        with pytest.raises(OSError): # This will need to be ValueError later
            local_neighborhood(network_file=Path(TEST_DIR, 'input', 'missing.txt'),
                               nodes_file=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
                               output_file=OUT_FILE)

    """
    Run the local neighborhood algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        with pytest.raises(ValueError):
            local_neighborhood(network_file=Path(TEST_DIR, 'input', 'ln-bad-network.txt'),
                               nodes_file=Path(TEST_DIR, 'input', 'ln-nodes.txt'),
                               output_file=OUT_FILE)

    # Write tests for the Local Neighborhood run function here.
    # The tests above test the internal python code for local_neighborhood - can you
    # write the `missing_file` and `ln` tests above but for Docker using LocalNeighborhood,
    # and at least one for Singularity?


    # """
    # Run the local neighborhood algorithm (Dockerized) on the example input files and check the output matches the expected output.
    # """
    # def test_local_neighborhood_run_docker_ln(self):
    #     OUT_FILE.unlink(missing_ok=True)
    #     LocalNeighborhoodWrapper.run(
    #         network=str(Path(TEST_DIR, 'input', 'ln-network.txt')),
    #         nodes=str(Path(TEST_DIR, 'input', 'ln-nodes.txt')),
    #         output_file=str(OUT_FILE),
    #         container_framework="docker"
    #     )
    #     assert OUT_FILE.exists(), 'Dockerized Local Neighborhood output file was not written'
    #     expected_file = Path(TEST_DIR, 'expected_output', 'ln-output.txt')
    #     assert cmp(OUT_FILE, expected_file, shallow=False), 'Dockerized output file does not match expected output file'

    # """
    # Run the local neighborhood algorithm (Dockerized) with a missing input file.
    # """
    # def test_local_neighborhood_run_docker_missing_file(self):
    #     with pytest.raises(ValueError):
    #         LocalNeighborhoodWrapper.run(
    #             network=str(Path(TEST_DIR, 'input', 'missing.txt')),
    #             nodes=str(Path(TEST_DIR, 'input', 'ln-nodes.txt')),
    #             output_file=str(OUT_FILE),
    #             container_framework="docker"
    #         )

    # """
    # Run the local neighborhood algorithm (Singularity) with a missing input file.
    # """
    # @pytest.mark.singularity # Test runs only if Singularity is configured/available
    # def test_local_neighborhood_run_singularity_missing_file(self):
    #     with pytest.raises(ValueError): 
    #         LocalNeighborhoodWrapper.run(
    #             network=str(Path(TEST_DIR, 'input', 'missing.txt')),
    #             nodes=str(Path(TEST_DIR, 'input', 'ln-nodes.txt')),
    #             output_file=str(OUT_FILE),
    #             container_framework="singularity"
    #         )
            
