import filecmp
from pathlib import Path
import os 

from spras import runner

# Define relative paths, which will be converted to absolute paths in setup_class
INDIR_RELATIVE = "input/"
OUTDIR_RELATIVE = "output/"
EXPDIR_RELATIVE = "expected/"
OI2_EDGE_CASES_INDIR_RELATIVE = 'input/omicsintegrator-edge-cases/'
DUPLICATE_EDGES_DIR_RELATIVE = 'input/duplicate-edges/'


algorithms = ['mincostflow', 'meo', 'omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'allpairs', 'domino', 'local_neighborhood']


class TestParseOutputs:
    # Define class variables for absolute paths
    PROJECT_ROOT = None
    INDIR_ABS = None
    OUTDIR_ABS = None
    EXPDIR_ABS = None
    OI2_EDGE_CASES_INDIR_ABS = None
    DUPLICATE_EDGES_DIR_ABS = None

    @classmethod
    def setup_class(cls):
        """
        Create the output directory and define absolute paths for tests.
        """
        cls.PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
        
        cls.INDIR_ABS = cls.PROJECT_ROOT / "test" / "parse-outputs" / INDIR_RELATIVE
        cls.OUTDIR_ABS = cls.PROJECT_ROOT / "test" / "parse-outputs" / OUTDIR_RELATIVE
        cls.EXPDIR_ABS = cls.PROJECT_ROOT / "test" / "parse-outputs" / EXPDIR_RELATIVE
        cls.OI2_EDGE_CASES_INDIR_ABS = cls.PROJECT_ROOT / "test" / "parse-outputs" / OI2_EDGE_CASES_INDIR_RELATIVE
        cls.DUPLICATE_EDGES_DIR_ABS = cls.PROJECT_ROOT / "test" / "parse-outputs" / DUPLICATE_EDGES_DIR_RELATIVE

        cls.OUTDIR_ABS.mkdir(parents=True, exist_ok=True)

    def test_parse_outputs(self):
        for algo in algorithms:
            # Use absolute paths for all functions
            test_file = self.INDIR_ABS / f"{algo}-raw-pathway.txt"
            out_file = self.OUTDIR_ABS / f"{algo}-pathway.txt"

            runner.parse_output(algo, str(test_file), str(out_file)) # Pass as string for all functions
            assert filecmp.cmp(str(self.OUTDIR_ABS / f"{algo}-pathway.txt"), str(self.EXPDIR_ABS / f"{algo}-pathway-expected.txt"), shallow=False)

    def test_empty_file(self):
        for algo in algorithms:
            test_file = self.INDIR_ABS / f"empty-raw-pathway.txt"
            out_file = self.OUTDIR_ABS / f"{algo}-empty-pathway.txt"

            runner.parse_output(algo, str(test_file), str(out_file)) 
            assert filecmp.cmp(str(self.OUTDIR_ABS / f"{algo}-empty-pathway.txt"), str(self.EXPDIR_ABS / f"empty-pathway-expected.txt"), shallow=False)

    def test_oi2_miss_insolution(self):
        test_file = self.OI2_EDGE_CASES_INDIR_ABS / f"omicsintegrator2-miss-insolution-raw-pathway.txt"
        out_file = self.OUTDIR_ABS / f"omicsintegrator2-miss-insolution-pathway.txt"

        runner.parse_output('omicsintegrator2', str(test_file), str(out_file)) 
        assert filecmp.cmp(str(out_file), str(self.EXPDIR_ABS / f"empty-pathway-expected.txt"), shallow=False)

    def test_oi2_wrong_order(self):
        test_file = self.OI2_EDGE_CASES_INDIR_ABS / f"omicsintegrator2-wrong-order-raw-pathway.txt"
        out_file = self.OUTDIR_ABS / f"omicsintegrator2-wrong-order-pathway.txt"

        runner.parse_output('omicsintegrator2', str(test_file), str(out_file)) 
        assert filecmp.cmp(str(out_file), str(self.EXPDIR_ABS / f"omicsintegrator2-pathway-expected.txt"), shallow=False)

    def test_duplicate_edges(self):
        for algo in algorithms:
            test_file = self.DUPLICATE_EDGES_DIR_ABS / f"{algo}-raw-pathway.txt"
            out_file = self.OUTDIR_ABS / f"{algo}-duplicate-pathway.txt"

            runner.parse_output(algo, str(test_file), str(out_file)) 
            assert filecmp.cmp(str(self.OUTDIR_ABS / f"{algo}-duplicate-pathway.txt"), str(self.EXPDIR_ABS / f"{algo}-pathway-expected.txt"), shallow=False)
