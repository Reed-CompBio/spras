# Run from SPRAS root with python -m test.analysis.test_summary

import pandas as pd
import os
from glob import glob
from src.analysis.summary.summary import summarize_networks

# Notes:
# - Column labels are required
# - 'NODEID' is required as the first column label
# - file_paths must be a list, even if a single file path is passed

# Make output directory
if not os.path.isdir("test/analysis/output"):
	os.makedirs("test/analysis/output")

# Toy networks
toy_network_files = glob("test/analysis/input/toy/*")
toy_node_table = pd.read_csv("test/analysis/input/toy_node_table.csv")
summarize_networks(toy_network_files, toy_node_table).to_csv("test/analysis/output/toy_summary.csv", index = False)

# Test data from example workflow:
example_network_files = glob("test/analysis/input/example/*")
example_node_table = pd.read_csv("test/analysis/input/example_node_table.csv")
summarize_networks(example_network_files, example_node_table).to_csv("test/analysis/output/example_summary.csv", index = False)


# Test data from EGFR workflow:
egfr_network_files = glob("test/analysis/input/egfr/*")
egfr_node_table = pd.read_csv("test/analysis/input/egfr_node_table.csv")
summarize_networks(egfr_network_files, egfr_node_table).to_csv("test/analysis/output/egfr_summary.csv", index = False)
