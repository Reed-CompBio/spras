from pathlib import Path

import pandas as pd

# set up necessary dataframes to run summarize_networks
import spras.config as config
from spras.analysis.summary import summarize_networks

# Notes:
# - Column labels are required in the node table
# - 'NODEID' is required as the first column label in the node table
# - file_paths must be a iterable, even if a single file path is passed

class TestSummary:
    # Test data from example workflow:
    def test_example_networks(self):
        config.init_from_file(Path("test/analysis/input/config.yaml"))
        algorithm_params = config.config.algorithm_params
        list(algorithm_params)
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in algorithm_params.items() for params_hash in param_combos.keys()]

        example_network_files = Path("test/analysis/input/example").glob("*.txt")
        example_node_table = pd.read_csv(Path("test/analysis/input/example_node_table.txt"), sep = "\t")
        example_output = pd.read_csv(Path("test/analysis/output/example_summary.txt"), sep = "\t")
        example_output["Name"] = example_output["Name"].map(convert_path)
        assert summarize_networks(example_network_files, example_node_table, algorithm_params, algorithms_with_params).equals(example_output)

    # Test data from EGFR workflow:
    def test_egfr_networks(self):
        config.init_from_file(Path("test/analysis/input/egfr.yaml"))
        algorithm_params = config.config.algorithm_params
        list(algorithm_params)
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in algorithm_params.items() for params_hash in param_combos.keys()]

        egfr_network_files = Path("test/analysis/input/egfr").glob("*.txt")
        egfr_node_table = pd.read_csv(Path("test/analysis/input/egfr_node_table.txt"), sep = "\t")
        egfr_output = pd.read_csv(Path("test/analysis/output/egfr_summary.txt"), sep = "\t")
        egfr_output["Name"] = egfr_output["Name"].map(convert_path)
        assert summarize_networks(egfr_network_files, egfr_node_table, algorithm_params, algorithms_with_params).equals(egfr_output)


# File paths have to be converted for the stored expected output files because otherwise the dataframes may not
# match if the test is run on a different operating system than the one used when the expected output was generated
# due to Linux versus Windows file path conventions
def convert_path(file_path):
    return str(Path(file_path))
