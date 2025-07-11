import os
import pickle as pkl
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_score,
    recall_score,
)

from spras.analysis.ml import create_palette


class Evaluation:
    NODE_ID = "NODEID"

    def __init__(self, gold_standard_dict: Dict):
        self.label = None
        self.datasets = None
        self.node_table = None
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
        for f in file_paths:
            df = pd.read_table(f, sep="\t", header=0, usecols=["Node1", "Node2"])
            y_pred = set(df['Node1']).union(set(df['Node2']))
            all_nodes = y_true.union(y_pred)
            y_true_binary = [1 if node in y_true else 0 for node in all_nodes]
            y_pred_binary = [1 if node in y_pred else 0 for node in all_nodes]
            # default to 0.0 if there is a divide by 0 error
            # not using precision_recall_curve because thresholds are binary (0 or 1); rather we are directly calculating precision and recall per pathway
            precision = precision_score(y_true_binary, y_pred_binary, zero_division=0.0)
            recall = recall_score(y_true_binary, y_pred_binary, zero_division=0.0)
            results.append({"Pathway": f, "Precision": precision, "Recall": recall})

        pr_df = pd.DataFrame(results)

        if not pr_df.empty:
            pr_df.sort_values(by=["Recall", "Pathway"], axis=0, ascending=True, inplace=True)
            pr_df.to_csv(output_file, sep="\t", index=False)
            if output_png is not None:
                plt.figure(figsize=(10, 7))
                color_palette = create_palette(algorithms)
                # plot a line per algorithm
                for algorithm in algorithms:
                    subset = pr_df[pr_df["Pathway"].str.contains(algorithm)]
                    if not subset.empty:
                        plt.plot(
                            subset["Recall"],
                            subset["Precision"],
                            color = color_palette[algorithm],
                            marker='o',
                            linestyle='',
                            label=f"{algorithm}"
                        )

                plt.xlabel("Recall")
                plt.ylabel("Precision")
                plt.xlim(-0.05, 1.05)
                plt.ylim(-0.05, 1.05)
                plt.title("Precision and Recall Plot")
                plt.legend()
                plt.grid(True)
                plt.savefig(output_png)
                plt.close()
        else:
            # SPRAS will hit this case if all the algorithms have 1 parameter combination
            # TODO: The Snakefile to use algorithms_mult_param_combos idea, how do we deal with an empty []?
            pr_df.to_csv(output_file, sep="\t", index=False)
            if output_png is not None:
                plt.figure(figsize=(10, 7))
                plt.plot([], [], label="No Pathways Given")
                plt.title("Precision and Recall Plot")
                plt.legend()
                plt.savefig(output_png)
                plt.close()

    @staticmethod
    def pca_chosen_pathway(coordinates_files: list, pathway_summary_file:str, output_dir:str):
        """
        Identifies the pathway closest to a specified highest kernel density estimated (kde) peak based on PCA coordinates
        Calculates the Euclidean distance from each data point to the KDE peak, then selects the closest pathway as the representative pathway.
        If there is more than one representative pathway, a tiebreaker will be used
            1) choose smallest pathway (smallest number of edges and nodes)
            2) end all be all, choose the first one based on name
        Returns a list of file paths for the representative pathway associated with the closest data point to the centroid.
        @param coordinates_files: a list of pca coordinates files for a dataset or specific algorithm in a dataset
        @param pathway_summary_file: a file for each file per dataset about its network statistics
        @param output_dir: the main reconstruction directory
        """
        rep_pathways = []

        for coordinates_file in coordinates_files:
            coord_df = pd.read_csv(coordinates_file, delimiter="\t", header=0)

            kde_peak_row = coord_df[coord_df['datapoint_labels'] == 'kde_peak']
            kde_peak = kde_peak_row.iloc[0, 1:].tolist()
            coord_df = coord_df[~coord_df['datapoint_labels'].isin(['kde_peak', 'centroid'])]

            pc_columns = [col for col in coord_df.columns if col.startswith('PC')]
            coord_df['Distance To KDE peak'] = np.sqrt(sum((coord_df[pc] - kde_peak[i]) ** 2 for i, pc in enumerate(pc_columns))).round(8)
            min_distance = coord_df["Distance To KDE peak"].min()
            candidates = coord_df[coord_df["Distance To KDE peak"] == min_distance]

            if len(candidates) == 1:
                closest_to_kde_peak = candidates.iloc[0]
            else:
                # add in summary stats file
                summary_stats_df = pd.read_csv(pathway_summary_file, sep="\t", header=0)
                summary_stats_df["Name"] = summary_stats_df["Name"].apply(lambda x: x.split("/")[-2])

                merged_df = candidates.merge(summary_stats_df, left_on="datapoint_labels", right_on="Name", how="inner")[["datapoint_labels", "PC1", "PC2", "Distance To KDE peak", "Number of edges", "Number of nodes"]]
                merged_df = merged_df.sort_values(by=["Number of edges", "Number of nodes", "datapoint_labels"], ascending=[True, True, True])

                # pick first one after full sorting
                closest_to_kde_peak = merged_df.iloc[0]

            rep_pathway = os.path.join(output_dir, f"{closest_to_kde_peak['datapoint_labels']}", "pathway.txt")
            rep_pathways.append(rep_pathway)

        return rep_pathways
