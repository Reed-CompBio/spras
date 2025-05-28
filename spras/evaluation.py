import os
import pickle as pkl
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)


class Evaluation:
    NODE_ID = "NODEID"

    def __init__(self, gold_standard_dict: Dict):
        self.label = None
        self.datasets = None
        self.node_table = None
        # self.edge_table = None TODO: later iteration
        self.load_files_from_dict(gold_standard_dict)
        return

    @staticmethod
    def merge_gold_standard_input(gs_dict, gs_file):
        """
        Merge files listed for this gold standard dataset and write the dataset to disk
        @param gs_dict: gold standard dataset to process
        @param gs_file: output filename
        """
        gs_dataset = Evaluation(gs_dict)
        gs_dataset.to_file(gs_file)

    def to_file(self, file_name):
        """
        Saves gold standard object to pickle file
        """
        with open(file_name, "wb") as f:
            pkl.dump(self, f)

    @staticmethod
    def from_file(file_name):
        """
        Loads gold standard object from a pickle file.
        Usage: gold_standard = Evaluation.from_file(pickle_file)
        """
        with open(file_name, "rb") as f:
            return pkl.load(f)

    def load_files_from_dict(self, gold_standard_dict: Dict):
        """
        Loads gold standard files from gold_standard_dict, which is one gold standard dataset
        dictionary from the list in the config file with the fields in the config file.
        Populates node_table.

        node_table is a single column of nodes pandas table.

        returns: none
        """
        self.label = gold_standard_dict["label"]  # cannot be empty, will break with a NoneType exception
        self.datasets = gold_standard_dict["dataset_labels"]  # can be empty, snakemake will not run evaluation due to dataset_gold_standard_pairs in snakemake file

        # cannot be empty, snakemake will run evaluation even if empty
        node_data_files = gold_standard_dict["node_files"][0]  # TODO: single file for now

        data_loc = gold_standard_dict["data_dir"]

        single_node_table = pd.read_table(os.path.join(data_loc, node_data_files), header=None)
        single_node_table.columns = [self.NODE_ID]
        self.node_table = single_node_table

        # TODO: are we allowing multiple node files or single in node_files for gs
        # if yes, a for loop is needed

        # TODO: later iteration - chose between node and edge file, or allow both

    @staticmethod
    def edge_frequency_node_ensemble(node_table: pd.DataFrame, ensemble_file: str):
        """
        Create a node ensemble using the edge ensemble frequencies by:
        1. Extracting Node1 and corresponding edge frequencies from the ensemble DataFrame.
        2. Appending Node2 and corresponding edge frequencies to include both sides of each undirected edge.
        3. Grouping by node and taking the maximum edge frequency per node.
        4. Adding any nodes from the gold standard (node_table) that are missing in the ensemble with a default frequency of 0.
        - If the node ensemble does not include all of the gold standard nodes, we cannot achieve full recall.
        @param node_table: the gold standard nodes
        @param ensemble_file: the edge ensemble file
        returns a node ensemble or an empty dataframe
        """
        ensemble_df = pd.read_table(ensemble_file, sep='\t', header=0)

        if not ensemble_df.empty:
            node1 = ensemble_df[['Node1', 'Frequency']].rename(columns={'Node1':'Node'})
            node2 = ensemble_df[['Node2', 'Frequency']].rename(columns={'Node2':'Node'})

            gs_nodes = node_table[['NODEID']].rename(columns={'NODEID':'Node'})
            gs_nodes['Frequency'] = 0.0

            all_nodes = pd.concat([node1, node2, gs_nodes])

            node_ensemble = all_nodes.groupby(['Node']).max().reset_index()
            return node_ensemble

        else:
            return pd.DataFrame(columns = ['Node', 'Frequency'])


    @staticmethod
    def precision_recall_curve_node_ensemble(node_ensemble:pd.DataFrame, node_table:pd.DataFrame, output_png: str):
        """
        Takes in a node ensemble for specific dataset or specific algorithm in a dataset, and an associated gold standard node table.
        Plots a precision and recall curve for the node ensemble against its associated gold standard node table
        Returns output back to output_png
        @param node_ensemble: the pre-computed node_ensemble
        @param node_table: the gold standard nodes
        @param output_png: the filename to save the precision and recall curves
        """
        gold_standard_nodes = set(node_table['NODEID'])

        if not node_ensemble.empty:
            y_true = [1 if node in gold_standard_nodes else 0 for node in node_ensemble['Node']]
            y_scores = node_ensemble['Frequency'].tolist()
            precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
            # avg precision summarizes a precision-recall curve as the weighted mean of precisions achieved at each threshold
            avg_precision = average_precision_score(y_true, y_scores)
            # the (number positives)/(number instances)
            baseline_precision = np.sum(y_true) / len(y_true)

            plt.figure()
            plt.plot(recall, precision, marker='o', label=f'Precision-Recall curve (AP:{avg_precision:.4f})')
            plt.axhline(y=baseline_precision, color='red', linestyle='--', label=f'Baseline: {baseline_precision:.4f}')
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title('Precision-Recall Curve')
            plt.legend()
            plt.grid(True)
            plt.savefig(output_png)
            plt.close()
        else:
            plt.figure()
            plt.plot([], [])
            plt.title("Precision-Recall Curve")
            plt.savefig(output_png)
            print("Empty ensemble file used")
            plt.close()
