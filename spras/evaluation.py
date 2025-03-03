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

    def select_max_freq_and_node(row: pd.Series):
        """
        Selects the node and frequency with the highest frequency value from two potential nodes in a row.
        Handles cases where one of the nodes or frequencies may be missing and returns the node associated with the maximum frequency.
        """
        max_freq = 0
        node = ""
        if pd.isna(row['Node2']) and pd.isna(row['Freq2']):
            max_freq = row['Freq1']
            node = row['Node1']
        elif pd.isna(row['Node1']) and pd.isna(row['Freq1']):
            max_freq = row['Freq2']
            node = row['Node2']
        else:
            max_freq = max(row['Freq1'], row['Freq2'])
            node = row['Node1']
        return node, max_freq

    def edge_frequency_node_ensemble(ensemble_file: str):
        """
        Processes an ensemble of edge frequencies to identify the highest frequency associated with each node
        Reads ensemble_file, separates frequencies by node, and then calculates the maximum frequency for each node.
        Returns a DataFrame of nodes with their respective maximum frequencies, or an empty DataFrame if ensemble_file is empty.
        @param ensemble_file: the pre-computed node_ensemble
        """
        ensemble_df = pd.read_table(ensemble_file, sep="\t", header=0)

        if not ensemble_df.empty:
            node1_freq = ensemble_df.drop(columns = ['Node2', 'Direction'])
            node2_freq = ensemble_df.drop(columns = ['Node1', 'Direction'])

            max_node1_freq = node1_freq.groupby(['Node1']).max().reset_index()
            max_node1_freq.rename(columns = {'Frequency': 'Freq1'}, inplace = True)
            max_node2_freq = node2_freq.groupby(['Node2']).max().reset_index()
            max_node2_freq.rename(columns = {'Frequency': 'Freq2'}, inplace = True)

            node_ensemble = max_node1_freq.merge(max_node2_freq, left_on='Node1', right_on='Node2', how='outer')
            node_ensemble[['Node', 'max_freq']] = node_ensemble.apply(Evaluation.select_max_freq_and_node, axis=1, result_type='expand')
            node_ensemble.drop(columns = ['Node1', 'Node2', 'Freq1', 'Freq2'], inplace = True)
            node_ensemble.sort_values('max_freq', ascending= False, inplace = True)
            return node_ensemble
        else:
            return pd.DataFrame(columns = ['Node', 'max_freq'])

    def precision_recall_curve_node_ensemble(node_ensemble:pd.DataFrame, node_table:pd.DataFrame, output_png: str):
        """
        Takes in an node ensemble for specific dataset or specific algorithm in a dataset, and an associated gold standard node table.
        Plots a precision and recall curve for the node ensemble against its associated gold standard node table
        Returns output back to output_png
        @param node_ensemble: the pre-computed node_ensemble
        @param node_table: the gold standard nodes
        @param output_file: the filename to save the precision and recall curves
        """
        gold_standard_nodes = set(node_table['NODEID'])

        if not node_ensemble.empty:
            y_true = [1 if node in gold_standard_nodes else 0 for node in node_ensemble['Node']]
            y_scores = node_ensemble['max_freq'].tolist()
            precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
            auc_precision_recall = average_precision_score(y_true, y_scores)

            plt.figure()
            plt.plot(recall, precision, marker='o', label='Precision-Recall curve')
            plt.axhline(y=auc_precision_recall, color='r', linestyle='--', label=f'Avg Precision: {auc_precision_recall:.4f}')
            plt.xlabel('Recall')
            plt.ylabel('Precision')
            plt.title('Precision-Recall Curve')
            plt.legend()
            plt.grid(True)
            plt.savefig(output_png)
        else:
            plt.figure()
            plt.plot([], [])
            plt.title("Empty Ensemble File")
            plt.savefig(output_png)