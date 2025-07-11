from pathlib import Path

import pytest
import subprocess
import shutil

import spras.config as config
from spras.analysis.cytoscape import run_cytoscape

config.init_from_file("test/analysis/input/example.yaml")

OUT_DIR = Path('test', 'analysis', 'output')
INPUT_DIR = Path('test', 'analysis', 'input', 'run', 'example')
INPUT_PATHWAYS = list(INPUT_DIR.rglob("pathway.txt"))
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

        subprocess.run(["snakemake", "--cores", "1", "--configfile", "test/analysis/input/example.yaml"])

    def test_cytoscape(self):
        out_path = Path(OUT_FILE)
        out_path.unlink(missing_ok=True)
        run_cytoscape(list(map(str, INPUT_PATHWAYS)), OUT_FILE)
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
        run_cytoscape(list(map(str, INPUT_PATHWAYS)), OUT_FILE, "singularity")
        assert out_path.exists()
    
    @classmethod
    def teardown_class(cls):
        shutil.rmtree(f"test/analysis/input/run/example")
