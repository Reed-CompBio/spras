import pytest
import pandas as pd
import os
from glob import glob
from src.analysis.summary.summary import summarize_networks

# Notes:
# - Column labels are required
# - 'NODEID' is required as the first column label
# - file_paths must be a list, even if a single file path is passed

class TestSummary:
	# Toy networks
	def test_toy_networks(self):
		toy_network_files = glob("test/analysis/input/toy/*")
		toy_node_table = pd.read_csv("test/analysis/input/toy_node_table.txt", sep = "\t")
		assert summarize_networks(toy_network_files, toy_node_table).equals(pd.read_csv("test/analysis/output/toy_summary.txt", sep = "\t"))

	# Test data from example workflow:
	def test_example_networks(self):
		example_network_files = glob("test/analysis/input/example/*")
		example_node_table = pd.read_csv("test/analysis/input/example_node_table.txt", sep = "\t")
		assert summarize_networks(example_network_files, example_node_table).equals(pd.read_csv("test/analysis/output/example_summary.txt", sep = "\t"))

	# Test data from EGFR workflow:
	def test_egfr_networks(self):
		egfr_network_files = glob("test/analysis/input/egfr/*")
		egfr_node_table = pd.read_csv("test/analysis/input/egfr_node_table.txt", sep = "\t")
		assert summarize_networks(egfr_network_files, egfr_node_table).equals(pd.read_csv("test/analysis/output/egfr_summary.txt", sep = "\t"))
