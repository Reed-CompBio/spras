import filecmp
import os
from pathlib import Path

import yaml

from spras import runner

OUTDIR_RELATIVE = "output/"
EXPDIR_RELATIVE = "expected/"

algo_exp_file = {
    'mincostflow': 'edges',
    'meo': 'edges',
    'omicsintegrator1': 'edges',
    'omicsintegrator2': 'edges',
    'domino': 'network',
    'pathlinker': 'network',
    'allpairs': 'network',
    'local_neighborhood': 'network'
}


class TestGenerateInputs:
    # Define class variables here, which will be populated in setup_class
    PROJECT_ROOT = None
    OUTDIR_ABS = None
    EXPDIR_ABS = None

    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory using absolute paths.
        """
        # Get the absolute path to the project root
        cls.PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
        
        # Construct absolute paths for OUTDIR and EXPDIR
        cls.OUTDIR_ABS = cls.PROJECT_ROOT / "test" / "generate-inputs" / OUTDIR_RELATIVE
        cls.EXPDIR_ABS = cls.PROJECT_ROOT / "test" / "generate-inputs" / EXPDIR_RELATIVE

        try:
            cls.OUTDIR_ABS.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error during directory creation for {cls.OUTDIR_ABS}: {e}")
            raise

    def test_prepare_inputs_networks(self):
        # Access class variables using cls.
        config_loc = self.PROJECT_ROOT / "test" / "generate-inputs" / "inputs" / "test_config.yaml"
        test_file = self.OUTDIR_ABS / "test_pickled_dataset.pkl" # Use OUTDIR_ABS for output file path

        with open(config_loc) as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        
        test_dataset = next((ds for ds in config["datasets"] if ds["label"] == "test_data"), None)
        runner.merge_input(test_dataset, test_file)

        for algo in algo_exp_file.keys():
            inputs = runner.get_required_inputs(algo)
            
            # Construct filename_map with absolute paths for the output files
            filename_map = {input_str: self.OUTDIR_ABS / f"{algo}-{input_str}.txt"
                            for input_str in inputs}

            runner.prepare_inputs(algo, test_file, filename_map)
            exp_file_name = algo_exp_file[algo]
            
            # Compare using absolute paths
            assert filecmp.cmp(self.OUTDIR_ABS / f"{algo}-{exp_file_name}.txt",
                               self.EXPDIR_ABS / f"{algo}-{exp_file_name}-expected.txt",
                               shallow=False)
