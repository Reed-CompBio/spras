import filecmp
import shutil
from pathlib import Path

from spras.config.config import Config
from spras.runner import algorithms, get_required_inputs, merge_input, prepare_inputs

OUTDIR = Path("test", "generate-inputs", "output")
EXPDIR = Path("test", "generate-inputs", "expected")

class TestGenerateInputs:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        if OUTDIR.exists():
            shutil.rmtree(OUTDIR)
        OUTDIR.mkdir(parents=True, exist_ok=True)

    def test_prepare_inputs_networks(self):
        config_loc = Path("test", "generate-inputs", "inputs", "test_config.yaml")

        config = Config.from_file(config_loc)
        test_file = Path("test", "generate-inputs", "output", "test_pickled_dataset.pkl")

        test_dataset = next((ds for ds in config.datasets.values() if ds.label == "test_data"), None)
        assert test_dataset is not None
        merge_input(test_dataset, test_file)

        for algo in algorithms.keys():
            inputs = get_required_inputs(algo)
            (OUTDIR / algo).mkdir(exist_ok=True)
            filename_map = {input_str: str(OUTDIR / algo / f"{algo}-{input_str}.txt") for input_str in inputs}
            prepare_inputs(algo, test_file, filename_map)
            required_inputs = algorithms[algo].required_inputs
            for exp_file_name in required_inputs:
                assert filecmp.cmp(OUTDIR / algo / f"{algo}-{exp_file_name}.txt", EXPDIR / algo / f"{algo}-{exp_file_name}-expected.txt",
                                   shallow=False), f"{algo} for {exp_file_name}.txt does not match up!"
