import filecmp
from pathlib import Path

from spras import runner

INDIR = "test/parse-outputs/input/"
OUTDIR = "test/parse-outputs/output/"
EXPDIR = "test/parse-outputs/expected/"

# DOMINO input is the concatenated module_0.html and module_1.html file from
# the DOMINO output of the network dip.sif and the nodes tnfa_active_genes_file.txt
# from https://github.com/Shamir-Lab/DOMINO/tree/master/examples

algorithms = ['mincostflow', 'meo', 'omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'allpairs', 'domino', 'local-neighborhood']


class TestParseOutputs:
    @classmethod
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
            assert filecmp.cmp(OUTDIR + f"{algo}-pathway.txt", EXPDIR + f"{algo}-pathway-expected.txt", shallow=False)
