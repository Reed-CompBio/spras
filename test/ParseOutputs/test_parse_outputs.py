import filecmp
import os
import shutil
from pathlib import Path

import yaml

from src import runner
from src.domino import DOMINO, post_domino_id_transform, pre_domino_id_transform

INDIR = "test/ParseOutputs/input/"
OUTDIR = "test/ParseOutputs/output/"
EXPDIR = "test/ParseOutputs/expected/"

# for domino
OUT_FILE_PARSE = OUTDIR+'/domino-parse-output.txt'
OUT_FILE_PARSE_EXP = EXPDIR + '/domino-parse-output.txt'

# domino is seperate function
algorithms = ['mincostflow', 'meo', 'omicsintegrator1', "omicsintegrator2", "pathlinker", "allpairs"]
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
            print(out_file)
            runner.parse_output(algo, test_file, out_file)
            assert filecmp.cmp(OUTDIR +f"{algo}-pathway.txt", EXPDIR + f"{algo}-pathway-expected.txt")

    def test_domino_parse_output(self):
        # Input is the concatenated module_0.html and module_1.html file from
        # the DOMINO output of the network dip.sif and the nodes tnfa_active_genes_file.txt
        # from https://github.com/Shamir-Lab/DOMINO/tree/master/examples
        # Confirms the generated output matches the expected output
        out_path = Path(OUT_FILE_PARSE)
        out_path.unlink(missing_ok=True)
        DOMINO.parse_output(
            INDIR+ 'domino-concat-modules.txt',
            OUT_FILE_PARSE)
        assert filecmp.cmp(OUT_FILE_PARSE, OUT_FILE_PARSE_EXP, shallow=False)
