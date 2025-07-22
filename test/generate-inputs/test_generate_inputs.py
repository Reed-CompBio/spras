import filecmp
import os
from pathlib import Path

import yaml

from spras import runner

OUTDIR = Path("test", "generate-inputs", "output")
EXPDIR = Path("test", "generate-inputs", "expected")

algo_exp_file: dict[str, str | list[str]] = {
    'mincostflow': 'edges',
    'meo': 'edges',
    'omicsintegrator1': 'edges',
    'omicsintegrator2': 'edges',
    'domino': 'network',
    'pathlinker': 'network',
    'allpairs': 'network',
    'bowtiebuilder': 'edges',
    'robust': ['network', 'scores', 'seeds'],
    'strwr': 'network',
    'rwr': 'network'
}


class TestGenerateInputs:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        OUTDIR.mkdir(parents=True, exist_ok=True)

    def test_prepare_inputs_networks(self):
        config_loc = Path("test", "generate-inputs", "inputs", "test_config.yaml")

        with config_loc.open() as config_file:
            config = yaml.load(config_file, Loader=yaml.FullLoader)
        test_file = "test/generate-inputs/output/test_pickled_dataset.pkl"

        test_dataset = next((ds for ds in config["datasets"] if ds["label"] == "test_data"), None)
        runner.merge_input(test_dataset, test_file)

        for algo, exp_file_names in algo_exp_file.items():
            inputs = runner.get_required_inputs(algo)
            filename_map = {input_str: os.path.join("test", "generate-inputs", "output", f"{algo}-{input_str}.txt")
                            for input_str in inputs}

            # clean up inputs
            for exp_file_name in exp_file_names:
                (OUTDIR / f"{algo}-{exp_file_name}.txt").unlink(missing_ok=True)

            runner.prepare_inputs(algo, test_file, filename_map)
            if isinstance(exp_file_names, str):
                exp_file_names = [exp_file_names]
            for exp_file_name in exp_file_names:
                output_file = OUTDIR / f"{algo}-{exp_file_name}.txt"
                expected_file = EXPDIR / f"{algo}-{exp_file_name}-expected.txt"
                assert filecmp.cmp(output_file, expected_file, shallow=False)

            for file in filename_map.values():
                assert Path(file).exists()
