import filecmp
import os
from pathlib import Path

import yaml

from spras import runner

OUTDIR = "test/generate-inputs/output/"
EXPDIR = "test/generate-inputs/expected/"

algo_exp_file = {
    'mincostflow': 'edges',
    'meo': 'edges',
    'omicsintegrator1': 'edges',
    'omicsintegrator2': 'edges',
    'domino': 'network',
    'pathlinker': 'network',
    'allpairs': 'network',
    'local-neighborhood': 'network'
    }


class TestGenerateInputs:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUTDIR).mkdir(parents=True, exist_ok=True)

    def test_prepare_inputs_networks(self):
        config_loc = os.path.join("config", "config.yaml")

        with open(config_loc) as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        test_file = "test/generate-inputs/output/test_pickled_dataset.pkl"

        data0_dataset = next((ds for ds in config["datasets"] if ds["label"] == "data0"), None)
        runner.merge_input(data0_dataset, test_file)

        for algo in algo_exp_file.keys():
            inputs = runner.get_required_inputs(algo)
            filename_map = {input_str: os.path.join("test", "generate-inputs", "output", f"{algo}-{input_str}.txt")
                            for input_str in inputs}
            runner.prepare_inputs(algo, test_file, filename_map)
            exp_file_name = algo_exp_file[algo]
            assert filecmp.cmp(OUTDIR + f"{algo}-{exp_file_name}.txt", EXPDIR + f"{algo}-{exp_file_name}-expected.txt",
                               shallow=False)
