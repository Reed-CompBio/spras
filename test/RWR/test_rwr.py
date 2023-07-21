import shutil
from pathlib import Path

import pytest

from src.rwr import RWR

TEST_DIR = 'test/RWR/'
OUT_FILES_1 = TEST_DIR + 'output/output2/rwr_pathway.txt'
OUT_FILES_2 = TEST_DIR + 'output/output1/rwr_pathway.txt'


class TestRWR:
    """
    Run the RWR algorithm on the example input files
    """

    def test_rwr_required(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Only include required arguments
        RWR.run(edges=TEST_DIR + 'input/' + '/edges.txt',
                        single_source='1',
                        prizes=TEST_DIR + 'input/' + '/prizes.txt',
                        output_file=OUT_FILES_1)
        assert out_path.exists()

    def test_rwr_alternative_graph(self):
        out_path = Path(OUT_FILES_2)
        out_path.unlink(missing_ok=True)
        RWR.run(edges=TEST_DIR + 'input/' + '/edges1.txt',
                        single_source='1',
                        prizes=TEST_DIR + 'input/' + '/prizes1.txt',
                        output_file=OUT_FILES_2)
        assert out_path.exists()

    def test_rwr_alternative_graph(self):
        out_path = Path(OUT_FILES_2)
        out_path.unlink(missing_ok=True)
        RWR.run(edges=TEST_DIR + 'input/' + '/edges1.txt',
                        single_source='0',
                        prizes=TEST_DIR + 'input/' + '/prizes1.txt',
                        df = 0.8,
                        w = 0.3,
                        output_file=OUT_FILES_2)
        assert out_path.exists()

    def test_rwr_all_optional(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Include all optional arguments
        RWR.run(edges=TEST_DIR + 'input/' + '/edges1.txt',
                        single_source='0',
                        prizes=TEST_DIR + 'input/' + '/prizes1.txt',
                        output_file=OUT_FILES_1,
                        df = 0.8,
                        f = 'sum',
                        w = 0.3,
                        threshold= 0.1)
        assert out_path.exists()


    def test_rw_missing(self):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            # No edges file
            RWR.run(single_source='1',
                            output_file=OUT_FILES_1)

    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_rwr_singularity(self):
        out_path = Path(OUT_FILES_1)
        out_path.unlink(missing_ok=True)
        # Only include required arguments and run with Singularity
        RWR.run(edges=TEST_DIR + 'input/' + '/edges1.txt',
                        single_source='1',
                        prizes=TEST_DIR + 'input/' + '/prizes1.txt',
                        output_file=OUT_FILES_2)
        assert out_path.exists()
