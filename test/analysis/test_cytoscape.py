from pathlib import Path

import pytest

import spras.config as config
from spras.analysis.cytoscape import run_cytoscape

config.init_from_file("test/analysis/input/config.yaml")

OUT_DIR = 'test/analysis/output/'
INPUT_DIR = 'test/analysis/input/example/'
INPUT_PATHWAYS = [INPUT_DIR + 'data0-meo-params-GKEDDFZ_pathway.txt',
                  INPUT_DIR + 'data0-omicsintegrator1-params-E3LSEZQ_pathway.txt',
                  INPUT_DIR + 'data0-omicsintegrator1-params-NFIPHUX_pathway.txt',
                  INPUT_DIR + 'data0-omicsintegrator2-params-IV3IPCJ_pathway.txt',
                  INPUT_DIR + 'data0-pathlinker-params-6SWY7JS_pathway.txt',
                  INPUT_DIR + 'data0-pathlinker-params-VQL7BDZ_pathway.txt']
OUT_FILE = 'test/analysis/output/cytoscape.cys'


class TestCytoscape:
    """
    Test creating a Cytoscape session file from a list of pathways
    """

    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_cytoscape(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        run_cytoscape(INPUT_PATHWAYS, OUT_FILE)
        assert out_path.exists()

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    # @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    # See https://github.com/Reed-CompBio/spras/pull/66#issuecomment-1730079719 for discussion of the test
    # environment where this test passes. It fails in GitHub Actions.
    # Open a GitHub issue if Cytoscape does not work on Singularity as expected for assistance debugging
    @pytest.mark.xfail(reason='Requires Singularity and only works for certain Singularity configurations')
    def test_cytoscape_singularity(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        run_cytoscape(INPUT_PATHWAYS, OUT_FILE, "singularity")
        assert out_path.exists()
