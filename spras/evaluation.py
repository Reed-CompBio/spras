import os
import pickle as pkl
import warnings
from pathlib import Path
from typing import Iterable

import pandas as pd
from sklearn.metrics import precision_score


class Evaluation:
    NODE_ID = "NODEID"

    def __init__(self, gold_standard_dict):
        self.label = None
        self.node_table = None
        # self.edge_table = None TODO: later iteration
        self.load_files_from_dict(gold_standard_dict)
        self.datasets = None
        return

    def to_file(self, file_name):
        """
        Saves gold standard object to pickle file
        """
        with open(file_name, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def from_file(cls, file_name):
        """
        Loads gold standard object from a pickle file.
        Usage: gold_standard = Evaluation.from_file(pickle_file)
        """
        with open(file_name, "rb") as f:
            return pkl.load(f)

    def load_files_from_dict(self, gold_standard_dict):
        """
        Loads gold standard files from gold_standard_dict, which is one gold standard dataset
        dictionary from the list in the config file with the fields in the config file.
        Populates node_table.

        node_table is a single column of nodes pandas table.

        returns: none
        """
        self.label = gold_standard_dict["label"]
        self.datasets = gold_standard_dict["datasets"]

        node_data_files = gold_standard_dict["node_files"][0] # TODO: single file for now
        data_loc = gold_standard_dict["data_dir"]

        single_node_table = pd.read_table(os.path.join(data_loc, node_data_files), header=None)
        single_node_table.columns = [self.NODE_ID]
        self.node_table = single_node_table

        # TODO: are we allowing multiple node files or single in node_files for gs
        # if yes, a for loop is needed

        # TODO: later iteration - chose between node and edge file, or allow both

    def precision(file_paths: Iterable[Path], node_table: pd.DataFrame, output_file: str):
        """
        Takes in file paths for a specific dataset and an associated gold standard node table.
        Calculates precision for each pathway file
        Returns output back to output_file
        @param file_paths: file paths of pathway reconstruction algorithm outputs
        @param node_table: the gold standard nodes
        @param output_file: the filename to save the precision of each pathway
        """
        y_true = node_table['NODEID'].tolist()
        results = []

        for file in file_paths:
            df = pd.read_table(file, sep="\t", header = 0, usecols=["Node1", "Node2"])
            y_pred = list(set(df['Node1']).union(set(df['Node2'])))
            all_nodes = set(y_true).union(set(y_pred))
            y_true_binary = [1 if node in y_true else 0 for node in all_nodes]
            y_pred_binary = [1 if node in y_pred else 0 for node in all_nodes]

            precision = precision_score(y_true_binary, y_pred_binary, zero_division=0.0)

            results.append({"Pathway": file, "Precision": precision})

        precision_df = pd.DataFrame(results)
        precision_df.to_csv(output_file, sep="\t", index=False)
