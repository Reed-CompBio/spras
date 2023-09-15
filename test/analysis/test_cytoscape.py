import shutil
from pathlib import Path

import pytest

from src.analysis.cytoscape import run_cytoscape

INPUT_DIR = 'test/analysis/input/example/'
INPUT_PATHWAYS = [INPUT_DIR + 'data0-meo-params-GKEDDFZ_pathway.txt',
                  INPUT_DIR + 'data0-omicsintegrator1-params-RQCQ4YN_pathway.txt',
                  INPUT_DIR + 'data0-omicsintegrator1-params-WY4V42C_pathway.txt',
                  INPUT_DIR + 'data0-omicsintegrator2-params-IV3IPCJ_pathway.txt',
                  INPUT_DIR + 'data0-pathlinker-params-6SWY7JS_pathway.txt',
                  INPUT_DIR + 'data0-pathlinker-params-VQL7BDZ_pathway.txt']
OUT_FILE = 'test/analysis/output/cytoscape.cys'


class TestCytoscape:
    """
    Test creating a Cytoscape session file from a list of pathways
    """
    def test_cytoscape(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        run_cytoscape(INPUT_PATHWAYS, OUT_FILE)
        assert out_path.exists()

    # Only run Singularity test if the binary is available on the system
    # spython is only available on Unix, but do not explicitly skip non-Unix platforms
    @pytest.mark.skipif(not shutil.which('singularity'), reason='Singularity not found on system')
    def test_cytoscape_singularity(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        run_cytoscape(INPUT_PATHWAYS, OUT_FILE, True)
        assert out_path.exists()
