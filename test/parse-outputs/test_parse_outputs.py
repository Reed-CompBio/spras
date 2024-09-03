import filecmp
from pathlib import Path

from spras import runner

INDIR = "test/parse-outputs/input/"
OUTDIR = "test/parse-outputs/output/"
EXPDIR = "test/parse-outputs/expected/"
RAW_PATHS_INDIR = 'test/parse-outputs/input/oi2-raw-pathways/'
RAW_PATHS_EXPDIR = 'test/parse-outputs/expected/oi2-expected/'

# DOMINO input is the concatenated module_0.html and module_1.html file from
# the DOMINO output of the network dip.sif and the nodes tnfa_active_genes_file.txt
# from https://github.com/Shamir-Lab/DOMINO/tree/master/examples

algorithms = ['mincostflow', 'meo', 'omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'allpairs', 'domino']

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

    def test_empty_file(self):
        for algo in algorithms:
            test_file = INDIR + f"empty-raw-pathway.txt"
            out_file = OUTDIR + f"{algo}-empty-pathway.txt"

            runner.parse_output(algo, test_file, out_file)
            assert filecmp.cmp(OUTDIR + f"{algo}-empty-pathway.txt", EXPDIR + f"empty-pathway-expected.txt", shallow=False)

    def test_oi2_correct_parse_output(self):
        test_file = RAW_PATHS_INDIR + f"oi2-correct.txt"
        out_file = OUTDIR + f"oi2-correct-pathway.txt"
        runner.parse_output('omicsintegrator2', test_file, out_file)
        assert filecmp.cmp(out_file, RAW_PATHS_EXPDIR + f"oi2-expected.txt", shallow=False)

    def test_oi2_empty_parse_output(self):
        test_file = RAW_PATHS_INDIR + f"oi2-empty.txt"
        out_file = OUTDIR + f"oi2-empty-pathway.txt"
        runner.parse_output('omicsintegrator2', test_file, out_file)
        assert filecmp.cmp(out_file, RAW_PATHS_EXPDIR + f"oi2-expected-empty.txt", shallow=False)

    def test_oi2_miss_insolution_parse_output(self):
        test_file = RAW_PATHS_INDIR + f"oi2-miss-insolution.txt"
        out_file = OUTDIR + f"oi2-miss-insolution-pathway.txt"
        runner.parse_output('omicsintegrator2', test_file, out_file)
        assert filecmp.cmp(out_file, RAW_PATHS_EXPDIR + f"oi2-expected-empty.txt", shallow=False)

    def test_oi2_wrong_order_parse_output(self):
        test_file = RAW_PATHS_INDIR + f"oi2-wrong-order.txt"
        out_file = OUTDIR + f"oi2-wrong-order-pathway.txt"
        runner.parse_output('omicsintegrator2', test_file, out_file)
        assert filecmp.cmp(out_file, RAW_PATHS_EXPDIR + f"oi2-expected-empty.txt", shallow=False)