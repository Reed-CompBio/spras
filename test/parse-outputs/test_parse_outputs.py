import filecmp
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

# algorithms is a list of implemented algorithms, and their dataset parameter, if any
algorithms: dict[str, Dataset] = {
    'mincostflow': None,
    'meo': None,
    'omicsintegrator1': None,
    'omicsintegrator2': None,
    'pathlinker': None,
    'allpairs': None,
    'domino': None,
    'diamond': Dataset({
        'label': 'test_dataset',
        'node_files': ['diamond-dataset-prizes.txt', 'diamond-dataset-sources.txt', 'diamond-dataset-targets.txt'],
        'edge_files': ['diamond-dataset-network.txt'],
        'data_dir': INDIR / 'dataset'
    }),
}

def get_dataset(algo, dataset: tuple[str, bool]) -> Dataset:
    return Dataset({
        'label': 'test_dataset'
    })

class TestParseOutputs:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        OUTDIR.mkdir(parents=True, exist_ok=True)

    def test_parse_outputs(self):
        for algo, dataset in algorithms.items():
            test_file = INDIR / f"{algo}-raw-pathway.txt"
            out_file = OUTDIR / f"{algo}-pathway.txt"
            expected_file = EXPDIR / f"{algo}-pathway-expected.txt"

            runner.parse_output(algo, test_file, out_file, data_file=dataset, relaxed_data_file=True)
            assert filecmp.cmp(out_file, expected_file, shallow=False)

    def test_empty_file(self):
        for algo, dataset in algorithms.items():
            test_file = INDIR / f"empty-raw-pathway.txt"
            out_file = OUTDIR / f"{algo}-empty-pathway.txt"

            runner.parse_output(algo, test_file, out_file, data_file=dataset, relaxed_data_file=True)
            assert filecmp.cmp(OUTDIR / f"{algo}-empty-pathway.txt", EXPDIR / f"empty-pathway-expected.txt", shallow=False)

    def test_oi2_miss_insolution(self):
        test_file = OI2_EDGE_CASES_INDIR / f"omicsintegrator2-miss-insolution-raw-pathway.txt"
        out_file = OUTDIR / f"omicsintegrator2-miss-insolution-pathway.txt"

        runner.parse_output('omicsintegrator2', test_file, out_file, relaxed_data_file=True)
        assert filecmp.cmp(out_file, EXPDIR / f"empty-pathway-expected.txt", shallow=False)

    def test_oi2_wrong_order(self):
        test_file = OI2_EDGE_CASES_INDIR / f"omicsintegrator2-wrong-order-raw-pathway.txt"
        out_file = OUTDIR / f"omicsintegrator2-wrong-order-pathway.txt"

        runner.parse_output('omicsintegrator2', test_file, out_file, relaxed_data_file=True)
        assert filecmp.cmp(out_file, EXPDIR / f"omicsintegrator2-pathway-expected.txt", shallow=False)

    def test_duplicate_edges(self):
        for algo, dataset in algorithms.items():
            test_file = DUPLICATE_EDGES_DIR / f"{algo}-raw-pathway.txt"
            out_file = OUTDIR / f"{algo}-duplicate-pathway.txt"

            runner.parse_output(algo, test_file, out_file, data_file=dataset, relaxed_data_file=True)
            assert filecmp.cmp(OUTDIR / f"{algo}-duplicate-pathway.txt", EXPDIR / f"{algo}-pathway-expected.txt", shallow=False)
