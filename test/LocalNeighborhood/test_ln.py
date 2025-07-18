import platform
import sys
import warnings
from filecmp import cmp
from pathlib import Path

import pytest

import spras.config as config

config.init_from_file("config/config.yaml")

from spras.containers import run_container_docker
from spras.local_neighborhood import LocalNeighborhood

TEST_DIR = Path('test', 'LocalNeighborhood/')
OUT_FILE = Path(TEST_DIR, 'output', 'ln-output.txt')


class TestLocalNeighborhood:

    """
    Run the local neighborhood algorithm with a missing input file
    """
    def test_missing_file(self):
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.unlink(missing_ok=True)
        with pytest.raises(OSError):
           LocalNeighborhood.run(
            nodes=TEST_DIR/'input'/'missing-nodes.txt',
            network=TEST_DIR/'input'/'ln-network.txt',
            output_file=OUT_FILE
        )

    """
    Run the local neighborhood algorithm with an improperly formatted network file
    """
    def test_format_error(self):
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.unlink(missing_ok=True)
        with pytest.raises(ValueError):
            LocalNeighborhood.run(
            nodes=TEST_DIR/'input'/'ln-nodes.txt',
            network=TEST_DIR/'input'/'ln-bad-network.txt',
            output_file=OUT_FILE
        )


    # Write tests for the Local Neighborhood run function here
    def test_localneighborhood_run(self):
        """
        Run Localneighborhood with the run function and check the output matches the expected output
        """
        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUT_FILE.unlink(missing_ok=True)
        LocalNeighborhood.run(
            nodes=TEST_DIR/'input'/'ln-nodes.txt',
            network=TEST_DIR/'input'/'ln-network.txt',
            output_file=OUT_FILE
        )
        assert OUT_FILE.exists(), 'Output file was not written'
        expected_file = Path(TEST_DIR, 'expected_output','ln-output.txt')
        assert cmp(OUT_FILE, expected_file, shallow=False), 'Output file does not match expected output file'
    def test_localneighborhood_run_missing_inputs(self):
        """
        Ensures Localneighborhood.run raises error when missing required inputs
        """
        with pytest.raises((ValueError, OSError)):
            LocalNeighborhood.run(
                nodes = None,
                network = TEST_DIR/'input'/'ln-network.txt',
                output_file = OUT_FILE
            )
        with pytest.raises((ValueError, OSError)):
            LocalNeighborhood.run(
                nodes = TEST_DIR /'input'/'ln-nodes.txt',
                network = None,
                output_file = OUT_FILE
            )
        with pytest.raises((ValueError, OSError)):
            LocalNeighborhood.run(
                nodes = TEST_DIR /'input'/'ln-nodes.txt',
                network = TEST_DIR /'input'/'ln-network.txt',
                output_file = None
            )
    @pytest.mark.skipif(platform.system() != "Linux", reason="Singularity only supported on Linux")
    def test_localneighborhood_run_singularity(self):
        """
        Run LocalNeighborhppd with singularity container framework and check the output matches expected output
        """
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        LocalNeighborhood.run(
            nodes = TEST_DIR /'input'/'ln-nodes.txt',
            network = TEST_DIR /'input'/'ln-network.txt',
            output_file = OUT_FILE,
            container_framework = 'singularity'
        )
        assert out_path.exists()
