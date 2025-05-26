import shutil
from pathlib import Path

import pytest

import spras.config as config
from spras.responsenet import ResponseNet

config.init_from_file("config/config.yaml")

TEST_DIR = 'test/ResponseNet/'
OUT_FILE = TEST_DIR + 'output/responsenet-output.txt'


class TestResponseNet:

    # Speed up the tests by only running this test on all input graphs
    # The remaining tests run only on graph1
    @pytest.mark.parametrize('graph', ['graph1'])
    def test_responsenet_required(self, graph):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)

        ResponseNet.run(sources=TEST_DIR + 'input/' + graph + '/sources.txt',
                        targets=TEST_DIR + 'input/' + graph + '/targets.txt',
                        edges=TEST_DIR + 'input/' + graph + '/edges.txt',
                        output_file=OUT_FILE)
        assert out_path.exists()
        # TODO: assert for the output .equals expected_output instead of only testing
        # that the output file exists


    @pytest.mark.parametrize('graph', ['graph1'])
    def test_responsenet_all_optional(self, graph):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        # Include all optional arguments
        MinCostFlow.run(sources=TEST_DIR + 'input/' + graph + '/sources.txt',
                        targets=TEST_DIR + 'input/' + graph + '/targets.txt',
                        edges=TEST_DIR + 'input/' + graph + '/edges.txt',
                        OUT_FILE=OUT_FILE,
                        gamma=10,
                        _verbose=True,
                        _output_log = True,
                        _include_st = True)
        assert out_path.exists()

    @pytest.mark.parametrize('graph', ['graph1'])
    def test_mincostflow_missing(self, graph):
        # Test the expected error is raised when required arguments are missing
        with pytest.raises(ValueError):
            MinCostFlow.run(sources=TEST_DIR + 'input/' + graph + '/sources.txt',
                            targets=TEST_DIR + 'input/' + graph + '/targets.txt',
                            output_file=OUT_FILE)

