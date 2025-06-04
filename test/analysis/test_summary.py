import filecmp
from pathlib import Path

import pandas as pd

import spras.config as config
from spras.analysis.summary import summarize_networks
from spras.dataset import Dataset

# Notes:
# - Column labels are required in the node table
# - 'NODEID' is required as the first column label in the node table
# - file_paths must be an iterable, even if a single file path is passed

INPUT_DIR = 'test/analysis/input/'
OUT_DIR = 'test/analysis/output/'
EXPECT_DIR = 'test/analysis/expected_output/'


class TestSummary:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_example_networks(self):
        """Test data from example workflow"""
        example_dict = {"label": "data0",
                        "edge_files": ["network.txt"],
                        "node_files": ["node-prizes.txt", "sources.txt", "targets.txt"],
                        "data_dir": "input",
                        "other_files": []
                        }
        example_dataset = Dataset(example_dict)
        example_node_table = example_dataset.node_table
        config.init_from_file(INPUT_DIR + "config.yaml")
        algorithm_params = config.config.algorithm_params
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in
                                  algorithm_params.items() for params_hash in param_combos.keys()]

        example_network_files = Path(INPUT_DIR + "example").glob("*.txt")  # must be path to use .glob()

        out_path = Path(OUT_DIR + "test_example_summary.txt")
        out_path.unlink(missing_ok=True)
        summarize_example = summarize_networks(example_network_files, example_node_table, algorithm_params,
                                               algorithms_with_params)
        summarize_example["Name"] = summarize_example["Name"].map(convert_path_posix)
        summarize_example.to_csv(out_path, sep='\t', index=False)

        # Comparing the dataframes directly with equals does not match because of how the parameter
        # combinations column is loaded from disk. Therefore, write both to disk and compare the files.
        assert filecmp.cmp(out_path, EXPECT_DIR + "test_example_summary.txt", shallow=False)

    def test_egfr_networks(self):
        """Test data from EGFR workflow"""
        egfr_dict = {"label": "tps_egfr",
                     "edge_files": ["phosphosite-irefindex13.0-uniprot.txt"],
                     "node_files": ["tps-egfr-prizes.txt"],
                     "data_dir": "input",
                     "other_files": []
                     }

        egfr_dataset = Dataset(egfr_dict)
        egfr_node_table = egfr_dataset.node_table
        config.init_from_file(INPUT_DIR + "egfr.yaml")
        algorithm_params = config.config.algorithm_params
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in
                                  algorithm_params.items() for params_hash in param_combos.keys()]

        egfr_network_files = Path(INPUT_DIR + "egfr").glob("*.txt")  # must be path to use .glob()

        out_path = Path(OUT_DIR + "test_egfr_summary.txt")
        out_path.unlink(missing_ok=True)
        summarize_egfr = summarize_networks(egfr_network_files, egfr_node_table, algorithm_params,
                                            algorithms_with_params)
        summarize_egfr["Name"] = summarize_egfr["Name"].map(convert_path_posix)
        summarize_egfr.to_csv(out_path, sep="\t", index=False)

        # Comparing the dataframes directly with equals does not match because of how the parameter
        # combinations column is loaded from disk. Therefore, write both to disk and compare the files.
        assert filecmp.cmp(out_path, EXPECT_DIR + "test_egfr_summary.txt", shallow=False)

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
