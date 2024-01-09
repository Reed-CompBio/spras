from pathlib import Path

import pandas as pd

from spras.analysis.summary import summarize_networks

# Notes:
# - Column labels are required in the node table
# - 'NODEID' is required as the first column label in the node table
# - file_paths must be a iterable, even if a single file path is passed


class TestSummary:
	# Toy networks
	def test_toy_networks(self):
		toy_network_files = Path("test/analysis/input/toy").glob("*.txt")
		toy_node_table = pd.read_csv(Path("test/analysis/input/toy_node_table.txt"), sep = "\t")
		toy_output = pd.read_csv(Path("test/analysis/output/toy_summary.txt"), sep = "\t")
		toy_output["Name"] = toy_output["Name"].map(convert_path)
		assert summarize_networks(toy_network_files, toy_node_table).equals(toy_output)

	# Test data from example workflow:
	def test_example_networks(self):
		example_network_files = Path("test/analysis/input/example").glob("*.txt")
		example_node_table = pd.read_csv(Path("test/analysis/input/example_node_table.txt"), sep = "\t")
		example_output = pd.read_csv(Path("test/analysis/output/example_summary.txt"), sep = "\t")
		example_output["Name"] = example_output["Name"].map(convert_path)
		assert summarize_networks(example_network_files, example_node_table).equals(example_output)

	# Test data from EGFR workflow:
	def test_egfr_networks(self):
		egfr_network_files = Path("test/analysis/input/egfr").glob("*.txt")
		egfr_node_table = pd.read_csv(Path("test/analysis/input/egfr_node_table.txt"), sep = "\t")
		egfr_output = pd.read_csv(Path("test/analysis/output/egfr_summary.txt"), sep = "\t")
		egfr_output["Name"] = egfr_output["Name"].map(convert_path)
		assert summarize_networks(egfr_network_files, egfr_node_table).equals(egfr_output)


# File paths have to be converted for the stored expected output files because otherwise the dataframes may not
# match if the test is run on a different operating system than the one used when the expected output was generated
# due to Linux versus Windows file path conventions
def convert_path(file_path):
	return str(Path(file_path))
