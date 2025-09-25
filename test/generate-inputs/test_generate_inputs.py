import filecmp
import os
from pathlib import Path

import yaml

from spras import runner
from spras.util import extend_filename

OUTDIR = Path("test", "generate-inputs", "output")
EXPDIR = Path("test", "generate-inputs", "expected")

algo_exp_file = {
    'mincostflow': 'edges',
    'meo': 'edges',
    'omicsintegrator1': 'edges',
    'omicsintegrator2': 'edges',
    'domino': 'network.sif',
    'pathlinker': 'network',
    'allpairs': 'network',
    'bowtiebuilder': 'edges',
    'strwr': 'network',
    'rwr': 'network',
    'responsenet': 'edges'
}


class TestGenerateInputs:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        OUTDIR.mkdir(parents=True, exist_ok=True)

    def test_prepare_inputs_networks(self):
        config_loc = os.path.join("test", "generate-inputs", "inputs", "test_config.yaml")

        with open(config_loc) as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        test_file = "test/generate-inputs/output/test_pickled_dataset.pkl"

        test_dataset = next((ds for ds in config["datasets"] if ds["label"] == "test_data"), None)
        runner.merge_input(test_dataset, test_file)

        for algo in algo_exp_file.keys():
            inputs = runner.get_required_inputs(algo)
            filename_map = {input_str: os.path.join("test", "generate-inputs", "output", f"{algo}-{extend_filename(input_str)}")
                            for input_str in inputs}

            exp_file_name = extend_filename(algo_exp_file[algo])
            out_file = (OUTDIR / exp_file_name).with_stem(f"{algo}-{Path(exp_file_name).stem}")
            expected_file = (EXPDIR / exp_file_name).with_stem(f"{algo}-{Path(exp_file_name).stem}-expected")

            out_file.unlink(missing_ok=True)

            runner.prepare_inputs(algo, test_file, filename_map)

            assert filecmp.cmp(out_file, expected_file, shallow=False)

            for file in filename_map.values():
                assert Path(file).exists()
