import os
import pickle as pkl
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
)

from spras.analysis.ml import create_palette


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
    def edge_frequency_node_ensemble(node_table: pd.DataFrame, ensemble_files: list) -> dict:
        """
        Create a dictionary of node ensemble using the edge ensemble frequencies by:
        1. Extracting Node1 and corresponding edge frequencies from the ensemble DataFrame.
        2. Appending Node2 and corresponding edge frequencies to include both sides of each undirected edge.
        3. Grouping by node and taking the maximum edge frequency per node.
        4. Adding any nodes from the gold standard (node_table) that are missing in the ensemble with a default
           frequency of 0. If the node ensemble does not include all of the gold standard nodes, we cannot achieve full
           recall.
        5. Saves the node ensemble in a dictionary under its associated algorithm ensemble or combined ensemble.
        @param node_table: the gold standard nodes
        @param ensemble_files: the edge ensemble files
        returns a dictionary of node ensembles
        """
        node_ensembles_dict = dict()

        for ensemble_file in ensemble_files:
            label = ensemble_file.split("/")[-1].split("-")[0]
            ensemble_df = pd.read_table(ensemble_file, sep='\t', header=0)

            if not ensemble_df.empty:
                node1 = ensemble_df[['Node1', 'Frequency']].rename(columns={'Node1': 'Node'})
                node2 = ensemble_df[['Node2', 'Frequency']].rename(columns={'Node2': 'Node'})

                gs_nodes = node_table[['NODEID']].rename(columns={'NODEID': 'Node'})
                gs_nodes['Frequency'] = 0.0

                all_nodes = pd.concat([node1, node2, gs_nodes])

                node_ensemble = all_nodes.groupby(['Node']).max().reset_index()
                node_ensembles_dict[label] = node_ensemble

            else:
                node_ensembles_dict[label] = pd.DataFrame(columns=['Node', 'Frequency'])

        return node_ensembles_dict

    @staticmethod
    def precision_recall_curve_node_ensemble(node_ensembles: dict, node_table: pd.DataFrame, output_png: str,
                                             output_file: str):
        """
        Takes in a node ensemble for specific dataset or specific algorithm in a dataset, and an associated gold standard node table.
        Plots a precision and recall curve for the node ensemble against its associated gold standard node table
        Returns output back to output_png
        @param node_ensembles: the pre-computed node_ensembles
        @param node_table: the gold standard nodes
        @param output_png: the filename to save the precision and recall curves
        @param output_file: the filename to save the precision, recall, and threshold values
        """
        gold_standard_nodes = set(node_table['NODEID'])

        label_names = list(node_ensembles)
        color_palette = create_palette(label_names)

        plt.figure(figsize=(10, 7))

        dfs = []

        for label, node_ensemble in node_ensembles.items():

            if not node_ensemble.empty:
                y_true = [1 if node in gold_standard_nodes else 0 for node in node_ensemble['Node']]
                y_scores = node_ensemble['Frequency'].tolist()
                precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
                # avg precision summarizes a precision-recall curve as the weighted mean of precisions achieved at each threshold
                avg_precision = average_precision_score(y_true, y_scores)
                # the (number positives)/(number instances)
                baseline_precision = np.sum(y_true) / len(y_true)

                plt.plot(recall, precision, color=color_palette[label], marker='o',
                         label=f'{label} PR curve (AP: {avg_precision:.4f})')
                plt.axhline(y=baseline_precision, color=color_palette[label], linestyle='--',
                            label=f'{label} Baseline Precision: {baseline_precision:.4f}')

                data = {
                    'Threshold': thresholds,
                    'Precision': precision[:-1],
                    'Recall': recall[:-1],
                    'Average_Precison': avg_precision,
                    'Baseline_Precision': baseline_precision
                }

                if label != 'ensemble':
                    data['Algorithm'] = [label] * len(thresholds)
                    cols = ['Algorithm'] + [col for col in data if col != 'Algorithm']
                else:
                    cols = list(data.keys())

                df = pd.DataFrame(data)[cols]
                dfs.append(df)

            else:
                plt.plot([], [], color=color_palette[label], marker='o', label=f'{label} PR curve - Empty Ensemble')

                data = {
                    'Threshold': ["None"],
                    'Precision': ["None"],
                    'Recall': ["None"],
                    'Average_Precison': ["None"],
                    'Baseline_Precision': ["None"]
                }

                if label != 'ensemble':
                    data['Algorithm'] = [label]
                    cols = ['Algorithm'] + [col for col in data if col != 'Algorithm']
                else:
                    cols = list(data.keys())

                df = pd.DataFrame(data)[cols]
                dfs.append(df)

        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.title('Precision-Recall Curve')
        plt.legend(loc='lower left', bbox_to_anchor=(1, 0.5))
        plt.grid(True)
        plt.savefig(output_png, bbox_inches='tight')
        plt.close()

        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df.to_csv(output_file, index=False, header=True, sep="\t")
