import filecmp
import os
import shutil
from pathlib import Path

import yaml

from spras import runner
from spras.domino import DOMINO, post_domino_id_transform, pre_domino_id_transform

INDIR = "test/parse-outputs/input/"
OUTDIR = "test/parse-outputs/output/"
EXPDIR = "test/parse-outputs/expected/"

algorithms = ['mincostflow', 'meo', 'omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'allpairs', 'domino']
class TestParseOutputs:
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUTDIR).mkdir(parents=True, exist_ok=True)

    def test_parse_outputs(self):
        for algo in algorithms:
            test_file = INDIR + f"{algo}-raw-pathway.txt"
            out_file = OUTDIR + f"{algo}-pathway.txt"
            
            runner.parse_output(algo, test_file, out_file)
            assert filecmp.cmp(OUTDIR +f"{algo}-pathway.txt", EXPDIR + f"{algo}-pathway-expected.txt", shallow=False)
