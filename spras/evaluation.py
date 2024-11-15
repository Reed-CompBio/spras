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
    def precision_and_recall(file_paths: Iterable[Path], node_table: pd.DataFrame, algorithms: list, output_file: str, output_png:str=None):
        """
        Takes in file paths for a specific dataset and an associated gold standard node table.
        Calculates precision and recall for each pathway file
        Returns output back to output_file
        @param file_paths: file paths of pathway reconstruction algorithm outputs
        @param node_table: the gold standard nodes
        @param algorithms: list of algorithms used in current run of SPRAS
        @param output_file: the filename to save the precision and recall of each pathway
        @param output_png (optional): the filename to plot the precision and recall of each pathway (not a PRC)
        """
        y_true = set(node_table['NODEID'])
        results = []
        for file in file_paths:
            df = pd.read_table(file, sep="\t", header=0, usecols=["Node1", "Node2"])
            # TODO: do we want to include the pathways that are empty for evaluation / in the pr_df?
            y_pred = set(df['Node1']).union(set(df['Node2']))
            all_nodes = y_true.union(y_pred)
            y_true_binary = [1 if node in y_true else 0 for node in all_nodes]
            y_pred_binary = [1 if node in y_pred else 0 for node in all_nodes]
            # default to 0.0 if there is a divide by 0 error
            # not using precision_recall_curve because thresholds are binary (0 or 1); rather we are directly calculating precision and recall per pathway
            precision = precision_score(y_true_binary, y_pred_binary, zero_division=0.0)
            recall = recall_score(y_true_binary, y_pred_binary, zero_division=0.0)
            results.append({"Pathway": file, "Precision": precision, "Recall": recall})

        pr_df = pd.DataFrame(results)
        pr_df.sort_values(by=["Recall", "Pathway"], axis=0, ascending=True, inplace=True)
        pr_df.to_csv(output_file, sep="\t", index=False)

        num_of_algorithms_used = 0
        if output_png is not None:
            if not pr_df.empty:
                plt.figure(figsize=(8, 6))
                # plot a line per algorithm
                for algorithm in algorithms: #TODO I think there is a better way than doing this; using split on the filepaths doesn't work bc it is not adaptable
                    subset = pr_df[pr_df["Pathway"].str.contains(algorithm)]
                    if not subset.empty:
                        plt.plot(
                            subset["Recall"],
                            subset["Precision"],
                            marker='o',
                            linestyle='-',
                            label=f"{algorithm}"
                        )
                        num_of_algorithms_used += 1

                # plot overall precision and recall from all the algorithms
                if num_of_algorithms_used > 1:
                    plt.plot(pr_df["Recall"], pr_df["Precision"], marker='o', linestyle='-', color='b', label="Overall Precision-Recall")

                plt.xlabel("Recall")
                plt.ylabel("Precision")
                plt.title(f"Precision and Recall Plot")
                plt.legend()
                plt.grid(True)
                plt.savefig(output_png)
            else:
                plt.figure()
                plt.plot([], [])
                plt.title("Empty Pathway Files")
                plt.savefig(output_png)


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

    def pca_chosen_pathway(coordinates_file: str, output_dir:str):
        """
        Identifies the pathway closest to a specified centroid based on PCA coordinates
        Calculates the Euclidean distance from each data point to the centroid, then selects the closest pathway.
        Returns the file path for the representative pathway associated with the closest data point.
        @param coordinates_file: the pca coordinates file for a dataset or specific algorithm in a datset
        @param output_dir: the main reconstruction directory
        """
        coord_df = pd.read_csv(coordinates_file, delimiter="\t", header=0)

        centroid_row = coord_df[coord_df['datapoint_labels'] == 'centroid']
        centroid = centroid_row.iloc[0, 1:].tolist()
        coord_df = coord_df[coord_df['datapoint_labels'] != 'centroid']

        pc_columns = [col for col in coord_df.columns if col.startswith('PC')]
        coord_df['Distance To Centroid'] = np.sqrt(sum((coord_df[pc] - centroid[i]) ** 2 for i, pc in enumerate(pc_columns)))
        closest_to_centroid = coord_df.sort_values(by='Distance To Centroid').iloc[0]
        rep_pathway = [os.path.join(output_dir, f"{closest_to_centroid['datapoint_labels']}", "pathway.txt")]

        return rep_pathway
