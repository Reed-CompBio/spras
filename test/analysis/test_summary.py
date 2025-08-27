import filecmp
import shutil
import subprocess
from pathlib import Path

import pandas as pd
import pytest

import spras.config.config as config
from spras.analysis.summary import summarize_networks
from spras.dataset import Dataset

# Notes:
# - Column labels are required in the node table
# - 'NODEID' is required as the first column label in the node table
# - file_paths must be an iterable, even if a single file path is passed

INPUT_DIR = 'test/analysis/input/'
OUT_DIR = 'test/analysis/output/'
EXPECT_DIR = 'test/analysis/expected_output/'

@pytest.fixture(params=[
    "example", "egfr"
])
def snakemake_output(request):
    """
    This returns the paramaterized input,
    along with a guarantee (doubling as an integration test)
    that the files will exist.
    """
    request = request.param
    subprocess.run(["snakemake", "--cores", "1", "--configfile", f"test/analysis/input/{request}.yaml"])
    yield request
    shutil.rmtree(f"test/analysis/input/run/{request}")

class TestSummary:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_example_networks(self, snakemake_output):
        """Test data from provided workflow.

        This also has the double purpose as serving as a light integration test
        for Snakemake, using summary analysis as the correctness check.
        """

        config.init_from_file(INPUT_DIR + f"{snakemake_output}.yaml")
        example_dataset = Dataset(list(config.config.datasets.values())[0])
        example_node_table = example_dataset.node_table
        algorithm_params = config.config.algorithm_params
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in
                                  algorithm_params.items() for params_hash in param_combos.keys()]

        example_network_files = Path(INPUT_DIR, "run", snakemake_output).rglob("pathway.txt")

        out_path = Path(OUT_DIR, f"test_{snakemake_output}_summary.txt")
        out_path.unlink(missing_ok=True)
        summarize_out = summarize_networks(example_network_files, example_node_table, algorithm_params,
                                               algorithms_with_params)
        # We do some post-processing to ensure that we get a stable summarize_out, since the attached hash
        # is subject to variation (especially in testing) whenever the SPRAS commit revision gets changed
        summarize_out["Parameter combination"] = summarize_out["Parameter combination"].astype(str)
        summarize_out = summarize_out.drop(columns=["Name"])
        summarize_out = summarize_out.sort_values(by=["Parameter combination"])
        summarize_out.to_csv(out_path, sep='\t', index=False)

        # Comparing the dataframes directly with equals does not match because of how the parameter
        # combinations column is loaded from disk. Therefore, write both to disk and compare the files.
        assert filecmp.cmp(out_path, EXPECT_DIR + f"expected_{snakemake_output}_summary.txt", shallow=False)

    def test_load_dataset_dict(self):
        """Test loading files from dataset_dict"""
        example_dict = {"label": "data0",
                        "edge_files": ["network.txt"],
                        "node_files": ["node-prizes.txt", "sources.txt", "targets.txt"],
                        "data_dir": "input",
                        "other_files": []
                        }
        example_dataset = Dataset(example_dict)
        example_node_table = example_dataset.node_table

        # node_table contents are not generated consistently in the same order,
        # so we will check that the contents are the same, but row order doesn't matter
        expected_node_table = pd.read_csv((EXPECT_DIR + "expected_node_table.txt"), sep="\t")

        # ignore 'NODEID' column because this changes each time upon new generation
        cols_to_compare = [col for col in example_node_table.columns if col != "NODEID"]
        same_df = (
            example_node_table[cols_to_compare]
            .sort_values(by=cols_to_compare)
            .reset_index(drop=True)
            .equals(
                expected_node_table[cols_to_compare]
                .sort_values(by=cols_to_compare)
                .reset_index(drop=True)
            )
        )

        assert same_df


# PurePosixPath will not convert the separators in strings
def convert_path_posix(file_path: str) -> str:
    """
    File paths have to be converted to posix (Linux) style before writing to disk and checking if files match
    because the tests might be run on Windows
    @param file_path: input file path
    @return: string representation of converted file path
    """
    return file_path.replace("\\", "/")
