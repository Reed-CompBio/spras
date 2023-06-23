import shutil
from pathlib import Path

import pytest

from src.rwr import RWR
from src.util import compare_files

TEST_DIR = 'test/RWR/'
OUT_FILES_1 = TEST_DIR + 'output/output2/rwr_pathway.txt'
OUT_FILES_2 = TEST_DIR + 'output/output1/rwr_pathway.txt'


'''
Need to think of some test files to use for this test.
'''


class TestRWR:
    """
    Run the RWR algorithm on the example input files and check the output matches the expected output
    """

    # Write tests for the Local Neighborhood run function here

    # Speed up the tests by only running this test on all input graphs
    # The remaining tests run only on graph1

    """
    Run Random walk with restart in the Docker image
    """
    def test_rwr_required(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        RWR.run(sources=TEST_DIR + 'input/'  + '/source_nodes.txt',
                        targets=TEST_DIR + 'input/' + '/target_nodes.txt',
                        edges=TEST_DIR + 'input/' + '/edges.txt',
                        output_file=OUT_FILES_1)
        assert out_path.exists()

    def test_rwr_alternative_graph(self):
        out_path = Path(OUT_FILES_2)
        out_path.unlink(missing_ok=True)
        RWR.run(sources=TEST_DIR + 'input/'  + '/source_nodes1.txt',
                        targets=TEST_DIR + 'input/' + '/target_nodes1.txt',
                        edges=TEST_DIR + 'input/' + '/edges1.txt',
                        output_file=OUT_FILES_2)
        assert out_path.exists()

    def test_rwr_some_optional(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Include optional argument
        RWR.run(sources=TEST_DIR + 'input/'  + '/source_nodes.txt',
                        targets=TEST_DIR + 'input/' + '/target_nodes.txt',
                        edges=TEST_DIR + 'input/' + '/edges.txt',
                        output_file=OUT_FILES_1,
                        df = '0.7')
        assert out_path.exists()

    def test_rwr_all_optional(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Include all optional arguments
        RWR.run(sources=TEST_DIR + 'input/'  + '/source_nodes.txt',
                        targets=TEST_DIR + 'input/' + '/target_nodes.txt',
                        edges=TEST_DIR + 'input/' + '/edges.txt',
                        output_file=OUT_FILES_1,
                        df = '0.7',
                        f = 'sum')
        assert out_path.exists()


    def test_rw_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edges file
            RWR.run(sources=TEST_DIR + 'input/'  + '/source_nodes.txt',
                            targets=TEST_DIR + 'input/' + '/target_nodes.txt',
                            output_file=OUT_FILES_1)

    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_rwr_singularity(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        RWR.run(sources=TEST_DIR + 'input/'  + '/source_nodes.txt',
                        targets=TEST_DIR + 'input/' + '/target_nodes.txt',
                        edges=TEST_DIR + 'input/' + '/edges.txt',
                        output_file=OUT_FILES_1,
                        df = '0.7',
                        f = 'sum',
                        singularity=True)
        assert out_path.exists()
