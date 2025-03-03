from pathlib import Path

import pandas as pd
import spras 
# set up necessary dataframes to run summarize_networks
import spras.config as config
from spras.analysis.summary import summarize_networks
from spras.dataset import Dataset

# Notes:
# - Column labels are required in the node table
# - 'NODEID' is required as the first column label in the node table
# - file_paths must be a iterable, even if a single file path is passed

class TestSummary:
    # Test data from example workflow:
    def test_example_networks(self):
        example_dict = { "label" : "data0",
                         "edge_files" : ["network.txt"],
                         "node_files" : ["node-prizes.txt", "sources.txt", "targets.txt"],
                         "data_dir" : "input",
                         "other_files" : []
                       }
        example_dataset = Dataset(example_dict)
        print("DATASET: ", example_dataset.node_table)
        example_node_table = example_dataset.node_table
        config.init_from_file(Path("input/config.yaml"))
        algorithm_params = config.config.algorithm_params
        list(algorithm_params)
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in algorithm_params.items() for params_hash in param_combos.keys()]

        example_network_files = Path("test/analysis/input/example").glob("*.txt") # must be path to use .glob()
        #example_node_table = pd.read_csv(Path("test/analysis/input/example_node_table.txt"), sep = "\t")
        example_output = pd.read_csv("output/example_summary.txt", sep = "\t")
        example_output["Name"] = example_output["Name"].map(convert_path)
        assert summarize_networks(example_network_files, example_node_table, algorithm_params, algorithms_with_params).equals(example_output)

    # Test data from EGFR workflow:
    def test_egfr_networks(self):
        egfr_dict = { "label" : "tps_egfr",
                      "edge_files" : ["phosphosite-irefindex13.0-uniprot.txt"],
                      "node_files" : ["tps-egfr-prizes.txt"],
                      "data_dir" : "input",
                      "other_files" : []
                    }
        egfr_dataset = Dataset(egfr_dict)
        egfr_node_table = egfr_dataset.node_table
        config.init_from_file(Path("input/egfr.yaml"))
        algorithm_params = config.config.algorithm_params
        list(algorithm_params)
        algorithms_with_params = [f'{algorithm}-params-{params_hash}' for algorithm, param_combos in algorithm_params.items() for params_hash in param_combos.keys()]

        egfr_network_files = Path("test/analysis/input/egfr").glob("*.txt") # must be path to use .glob()
        #egfr_node_table = pd.read_csv(Path("test/analysis/input/egfr_node_table.txt"), sep = "\t")
        egfr_output = pd.read_csv(("output/egfr_summary.txt"), sep = "\t")
        egfr_output["Name"] = egfr_output["Name"].map(convert_path)
        assert summarize_networks(egfr_network_files, egfr_node_table, algorithm_params, algorithms_with_params).equals(egfr_output)

    # Test loading files from dataset_dict:
    def test_load_dataset_dict(self):
        example_dict = { "label" : "data0",
                         "edge_files" : ["network.txt"],
                         "node_files" : ["node-prizes.txt", "sources.txt", "targets.txt"],
                         "data_dir" : "input",
                         "other_files" : []
                       }
        example_node_table = Dataset(example_dict)
        example_node_table.load_files_from_dict(example_dict)

        #print(example_node_table) # debug statement
        example_expected = "temp" # temp

        assert True

# File paths have to be converted for the stored expected output files because otherwise the dataframes may not
# match if the test is run on a different operating system than the one used when the expected output was generated
# due to Linux versus Windows file path conventions
def convert_path(file_path):
    return str(Path(file_path))
