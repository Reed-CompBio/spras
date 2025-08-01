import filecmp
from glob import glob
from pathlib import Path

from spras import runner
from spras.dataset import Dataset

INDIR = Path("test", "parse-outputs", "input")
OUTDIR = Path("test", "parse-outputs", "output")
EXPDIR = Path("test", "parse-outputs", "expected")
OI2_EDGE_CASES_INDIR = Path('test', 'parse-outputs', 'input', 'omicsintegrator-edge-cases')
DUPLICATE_EDGES_DIR = Path('test', 'parse-outputs', 'input', 'duplicate-edges')
# DOMINO input is the concatenated module_0.html and module_1.html file from
# the DOMINO output of the network dip.sif and the nodes tnfa_active_genes_file.txt
# from https://github.com/Shamir-Lab/DOMINO/tree/master/examples

algorithms = {
    'mincostflow': {},
    'meo': {},
    'omicsintegrator1': {},
    'omicsintegrator2': {},
    'pathlinker': {},
    'allpairs': {},
    'domino': {},
    'bowtiebuilder': {},
    'responsenet': {},
    'strwr': {
        'threshold': 3,
        'dataset': Dataset({
            'label': 'test_dataset',
            'node_files': ['strwr-dataset-prizes.txt', 'strwr-dataset-sources.txt', 'strwr-dataset-targets.txt'],
            'edge_files': ['strwr-dataset-network.txt'],
            'other_files': [],
            'data_dir': INDIR / 'dataset' / 'strwr'
        })
    },
    'rwr': {
        'threshold': 2,
        'dataset': Dataset({
            'label': 'test_dataset',
            'node_files': ['rwr-dataset-prizes.txt', 'rwr-dataset-sources.txt', 'rwr-dataset-targets.txt'],
            'edge_files': ['rwr-dataset-network.txt'],
            'other_files': [],
            'data_dir': INDIR / 'dataset' / 'rwr'
        })
    }
}

class TestParseOutputs:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        OUTDIR.mkdir(parents=True, exist_ok=True)

    def test_parse_outputs(self):
        for algo, params in algorithms.items():
            test_file = INDIR / f"{algo}-raw-pathway.txt"
            out_file = OUTDIR / f"{algo}-pathway.txt"

            runner.parse_output(algo, test_file, out_file, params)
            assert filecmp.cmp(OUTDIR / f"{algo}-pathway.txt", EXPDIR / f"{algo}-pathway-expected.txt", shallow=False)

    def test_oi2_miss_insolution(self):
        test_file = OI2_EDGE_CASES_INDIR / f"omicsintegrator2-miss-insolution-raw-pathway.txt"
        out_file = OUTDIR / f"omicsintegrator2-miss-insolution-pathway.txt"

        runner.parse_output('omicsintegrator2', test_file, out_file, {})
        assert filecmp.cmp(out_file, EXPDIR / f"empty-pathway-expected.txt", shallow=False)

    def test_oi2_wrong_order(self):
        test_file = OI2_EDGE_CASES_INDIR / f"omicsintegrator2-wrong-order-raw-pathway.txt"
        out_file = OUTDIR / f"omicsintegrator2-wrong-order-pathway.txt"

        runner.parse_output('omicsintegrator2', test_file, out_file, {})
        assert filecmp.cmp(out_file, EXPDIR / f"omicsintegrator2-pathway-expected.txt", shallow=False)

    def test_duplicate_edges(self):
        for algo, params in algorithms.items():
            test_file = DUPLICATE_EDGES_DIR / f"{algo}-raw-pathway.txt"
            out_file = OUTDIR / f"{algo}-duplicate-pathway.txt"

            runner.parse_output(algo, test_file, out_file, params)
            assert filecmp.cmp(OUTDIR / f"{algo}-duplicate-pathway.txt", EXPDIR / f"{algo}-pathway-expected.txt", shallow=False)

    def test_empty_raw_pathway(self):
        for algo, params in algorithms.items():
            files = glob(str(INDIR / "empty" / f"{algo}-empty-raw-pathway*"))
            assert len(files) != 0, "can't test on no empty raw pathways!"
            for test_file in glob(str(INDIR / "empty" / f"{algo}-empty-raw-pathway*")):
                out_file = OUTDIR / f"{algo}-empty-pathway-output.txt"
                runner.parse_output(algo, test_file, out_file, params)
                assert filecmp.cmp(out_file, EXPDIR / f"empty-pathway-expected.txt", shallow=False)
