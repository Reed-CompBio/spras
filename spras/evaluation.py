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
    def precision_and_recall(file_paths: Iterable[Path], node_table: pd.DataFrame, algorithms: list, output_file: str,
                             output_png: str):
        """
        Takes in file paths for a specific dataset and an associated gold standard node table.
        Calculates precision and recall for each pathway file
        Returns output back to output_file
        @param file_paths: file paths of pathway reconstruction algorithm outputs
        @param node_table: the gold standard nodes
        @param algorithms: list of algorithms used in current run of SPRAS
        @param output_file: the filename to save the precision and recall of each pathway
        @param output_png: the filename to plot the precision and recall of each pathway (not a PRC)
        """
        y_true = set(node_table["NODEID"])
        results = []
        for f in file_paths:
            df = pd.read_table(f, sep="\t", header=0, usecols=["Node1", "Node2"])
            y_pred = set(df["Node1"]).union(set(df["Node2"]))
            all_nodes = y_true.union(y_pred)
            y_true_binary = [1 if node in y_true else 0 for node in all_nodes]
            y_pred_binary = [1 if node in y_pred else 0 for node in all_nodes]
            # default to 0.0 if there is a divide by 0 error
            # not using precision_recall_curve because thresholds are binary (0 or 1); rather we are directly
            # calculating precision and recall per pathway
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
                            color=color_palette[algorithm],
                            marker="o",
                            linestyle="",
                            label=f"{algorithm}"
                        )

                plt.xlabel("Recall")
                plt.ylabel("Precision")
                plt.xlim(-0.05, 1.05)
                plt.ylim(-0.05, 1.05)
                if "per-algorithm" in output_png:
                    plt.title("PCA-Chosen Pathway Per Algorithm Precision and Recall Plot")
                else:
                    plt.title("PCA-Chosen Pathway Precision and Recall Plot")
                plt.legend()
                plt.grid(True)
                plt.savefig(output_png)
                plt.close()
        else:
            # Edge case: if all algorithms chosen use only 1 parameter combination
            # TODO: once functions are separated, update to be a warning
            # See https://github.com/Reed-CompBio/spras/issues/331
            pr_df = pd.DataFrame(columns=["Pathway", "Precision", "Recall"])
            pr_df.to_csv(output_file, sep="\t", index=False, )
            if output_png is not None:
                plt.figure(figsize=(10, 7))
                plt.plot([], [], label="No Pathways Given")
                plt.title("Empty PCA-Chosen Precision and Recall Plot")
                plt.legend()
                plt.savefig(output_png)
                plt.close()

    @staticmethod
    def pca_chosen_pathway(coordinates_files: list, pathway_summary_file: str, output_dir: str):
        """
        Identifies the pathway closest to a specified highest kernel density estimated (KDE) peak based on PCA
        coordinates
        Calculates the Euclidean distance from each data point to the KDE peak, then selects the closest pathway as the
        representative pathway.
        If there is more than one representative pathway, a tiebreaker will be used
            1) choose smallest pathway (smallest number of edges and nodes)
            2) end all be all, choose the first one based on name
        Returns a list of file paths for the representative pathway associated with the closest data point to the
        centroid.
        @param coordinates_files: a list of PCA coordinates files for a dataset or specific algorithm in a dataset
        @param pathway_summary_file: a file for each file per dataset about its network statistics
        @param output_dir: the main reconstruction directory
        """
        rep_pathways = []

        for coordinates_file in coordinates_files:
            coord_df = pd.read_csv(coordinates_file, delimiter="\t", header=0)

            kde_peak_row = coord_df[coord_df["datapoint_labels"] == "kde_peak"]
            kde_peak = kde_peak_row.iloc[0, 1:].tolist()
            coord_df = coord_df[~coord_df["datapoint_labels"].isin(["kde_peak", "centroid"])]

            pc_columns = [col for col in coord_df.columns if col.startswith("PC")]
            coord_df["Distance To KDE peak"] = np.sqrt(sum((coord_df[pc] - kde_peak[i]) ** 2 for i, pc in enumerate(pc_columns))).round(8)
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

    @staticmethod
    def edge_frequency_node_ensemble(node_table: pd.DataFrame, ensemble_files: list, dataset_file: str) -> dict:
        """
        Generates a dictionary of node ensembles using edge frequency data from a list of ensemble files.
        A list of ensemble files can contain an aggregated ensemble or algorithm-specific ensembles per dataset

        1. Prepare a set of default nodes (from the interactome and gold standard) with frequency 0,
        ensuring all nodes are represented in the ensemble.
            - Answers "Did the algorithm(s) select the correct nodes from the entire network?"
            - It measures whether the algorithm(s) can distinguish relevant gold standard nodes
            from the full 'universe' of possible nodes present in the input network.
        2. For each edge ensemble file:
            a. Read edges and their frequencies.
            b. Convert edges frequencies into node-level frequencies for Node1 and Node2.
            c. Merge with the default node set and group by node, taking the maximum frequency per node.
        3. Store the resulting node-frequency ensemble under the corresponding ensemble source (label).

        If the interactome or gold standard table is empty, a ValueError is raised.

        @param node_table: dataFrame of gold standard nodes (column: NODEID)
        @param ensemble_files: list of file paths containing edge ensemble outputs
        @param dataset_file: path to the dataset file used to load the interactome
        @return: dictionary mapping each ensemble source to its node ensemble DataFrame
        """

        node_ensembles_dict = dict()

        pickle = Evaluation.from_file(dataset_file)
        interactome = pickle.get_interactome()

        if interactome.empty:
            raise ValueError(
                f"Cannot compute PR curve or generate node ensemble. Input network for dataset '{dataset_file.split('-')[0]}' is empty."
            )
        if node_table.empty:
            raise ValueError(
                f"Cannot compute PR curve or generate node ensemble. Gold standard associated with dataset '{dataset_file.split('-')[0]}' is empty."
            )

        # set the initial default frequencies to 0 for all interactome and gold standard nodes
        node1_interactome = interactome[['Interactor1']].rename(columns={'Interactor1': 'Node'})
        node1_interactome['Frequency'] = 0.0
        node2_interactome = interactome[['Interactor2']].rename(columns={'Interactor2': 'Node'})
        node2_interactome['Frequency'] = 0.0
        gs_nodes = node_table[[Evaluation.NODE_ID]].rename(columns={Evaluation.NODE_ID: 'Node'})
        gs_nodes['Frequency'] = 0.0

        # combine gold standard and network nodes
        other_nodes = pd.concat([node1_interactome, node2_interactome, gs_nodes])

        for ensemble_file in ensemble_files:
            label = Path(ensemble_file).name.split('-')[0]
            ensemble_df = pd.read_table(ensemble_file, sep='\t', header=0)

            if not ensemble_df.empty:
                node1 = ensemble_df[['Node1', 'Frequency']].rename(columns={'Node1': 'Node'})
                node2 = ensemble_df[['Node2', 'Frequency']].rename(columns={'Node2': 'Node'})
                all_nodes = pd.concat([node1, node2, other_nodes])
                node_ensemble = all_nodes.groupby(['Node']).max().reset_index()
            else:
                node_ensemble = other_nodes.groupby(['Node']).max().reset_index()

            node_ensembles_dict[label] = node_ensemble

        return node_ensembles_dict

    @staticmethod
    def precision_recall_curve_node_ensemble(node_ensembles: dict, node_table: pd.DataFrame, output_png: str,
                                             output_file: str):
        """
        Plots precision-recall (PR) curves for a set of node ensembles evaluated against a gold standard.

        Takes in a dictionary containing either algorithm-specific node ensembles or an aggregated node ensemble
        for a given dataset, along with the corresponding gold standard node table. Computes PR curves for
        each ensemble and plots all curves on a single figure.

        @param node_ensembles: dict of the pre-computed node_ensemble(s)
        @param node_table: gold standard nodes
        @param output_png: filename to save the precision and recall curves as a .png image
        @param output_file: filename to save the precision, recall, threshold values, average precision, and baseline
        average precision
        """
        gold_standard_nodes = set(node_table[Evaluation.NODE_ID])

        # make color palette per ensemble label name
        label_names = list(node_ensembles.keys())
        color_palette = create_palette(label_names)

        plt.figure(figsize=(10, 7))

        prc_dfs = []
        metric_dfs = []

        baseline = None

        for label, node_ensemble in node_ensembles.items():
            if not node_ensemble.empty:
                y_true = [1 if node in gold_standard_nodes else 0 for node in node_ensemble['Node']]
                y_scores = node_ensemble['Frequency'].tolist()
                precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
                # avg precision summarizes a precision-recall curve as the weighted mean of precisions achieved at each threshold
                avg_precision = average_precision_score(y_true, y_scores)

                # only set baseline precision once
                # the same for every algorithm per dataset/goldstandard pair
                if baseline is None:
                    baseline = np.sum(y_true) / len(y_true)
                    plt.axhline(y=baseline, color="black", linestyle='--', label=f'Baseline: {baseline:.4f}')

                plt.plot(recall, precision, color=color_palette[label], marker='o',
                         label=f'{label.capitalize()} (AP: {avg_precision:.4f})')

                # Dropping last elements because scikit-learn adds (1, 0) to precision/recall for plotting, not tied to real thresholds
                # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html#sklearn.metrics.precision_recall_curve:~:text=Returns%3A-,precision,predictions%20with%20score%20%3E%3D%20thresholds%5Bi%5D%20and%20the%20last%20element%20is%200.,-thresholds
                prc_data = {
                    'Threshold': thresholds,
                    'Precision': precision[:-1],
                    'Recall': recall[:-1],
                }

                metric_data = {
                    'Average_Precision': [avg_precision],
                }

                ensemble_source = label.capitalize() if label != 'ensemble' else "Aggregated"
                prc_data = {'Ensemble_Source': [ensemble_source] * len(thresholds), **prc_data}
                metric_data = {'Ensemble_Source': [ensemble_source], **metric_data}

                prc_df = pd.DataFrame.from_dict(prc_data)
                prc_dfs.append(prc_df)
                metric_df = pd.DataFrame.from_dict(metric_data)
                metric_dfs.append(metric_df)

            else:
                raise ValueError(
                    "Cannot compute PR curve: the ensemble network is empty."
                    f"This should not happen unless the input network for pathway reconstruction is empty."
                )

        if 'ensemble' not in label_names:
            plt.title('Precision-Recall Curve Per Algorithm Specific Ensemble')
        else:
            plt.title('Precision-Recall Curve for Aggregated Ensemble Across Algorithms')

        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.xlabel('Recall')
        plt.ylabel('Precision')
        plt.legend(loc='lower left', bbox_to_anchor=(1, 0.5))
        plt.grid(True)
        plt.savefig(output_png, bbox_inches='tight')
        plt.close()

        combined_prc_df = pd.concat(prc_dfs, ignore_index=True)
        combined_metrics_df = pd.concat(metric_dfs, ignore_index=True)
        combined_metrics_df["Baseline"] = baseline

        # merge dfs and NaN out metric values except for first row of each Ensemble_Source
        complete_df = combined_prc_df.merge(combined_metrics_df, on="Ensemble_Source", how="left")
        not_last_rows = complete_df.duplicated(subset="Ensemble_Source", keep='first')
        complete_df.loc[not_last_rows, ["Average_Precision", "Baseline"]] = None
        complete_df.to_csv(output_file, index=False, sep="\t")
