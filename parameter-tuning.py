import glob
import os
import pickle as pkl
from pathlib import Path
from typing import Dict, Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    PrecisionRecallDisplay,
    average_precision_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)

from spras.analysis.ml import summarize_networks
from spras.evaluation import Evaluation

# make directories
directories = ["parameter-tuning","parameter-tuning/ensembling-parameter-tuning", "parameter-tuning/no-parameter-tuning", "parameter-tuning/pca-parameter-tuning"]

for directory in directories:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Directory {directory} was created.")
    else:
        print(f"Directory {directory} already exists.")


# #################################################################################################################################################
# Parameter Tuning with Ensemble networks

def select_max_freq_and_node(row):
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

def precision_recall(file, node_table, node_freq_filename, output_file):
    gold_standard_nodes = set(node_table['NODEID'])

    df = pd.read_table(file, sep="\t", header=0)

    node1_freq = df.drop(columns = ['Node2', 'Direction'])
    node2_freq = df.drop(columns = ['Node1', 'Direction'])
    max_node1_freq = node1_freq.groupby(['Node1']).max().reset_index()
    max_node1_freq.rename(columns = {'Frequency': 'Freq1'}, inplace = True)
    max_node2_freq = node2_freq.groupby(['Node2']).max().reset_index()
    max_node2_freq.rename(columns = {'Frequency': 'Freq2'}, inplace = True)
    node_df_merged = max_node1_freq.merge(max_node2_freq, left_on='Node1', right_on='Node2', how='outer')
    node_df_merged[['Node', 'max_freq']] = node_df_merged.apply(select_max_freq_and_node, axis=1, result_type='expand')
    node_df_merged.drop(columns = ['Node1', 'Node2', 'Freq1', 'Freq2'], inplace = True)

    node_df_merged.sort_values('max_freq', ascending= False, inplace = True)
    node_df_merged.to_csv(node_freq_filename, sep = "\t",header=True, index=False)

    y_true = [1 if node in gold_standard_nodes else 0 for node in node_df_merged['Node']]
    y_scores = node_df_merged['max_freq'].tolist()

    # print(f"y_true:\n{y_true}")
    # print(f"y_score:\n{y_scores}")

    plt.figure()
    precision, recall, thresholds = precision_recall_curve(y_true, y_scores)
    # print(f"precision:{precision}\n recall:{recall}\n thresholds:{thresholds}\n")
    auc_precision_recall = average_precision_score(y_true, y_scores)

    plt.plot(recall, precision, marker='o', label='Precision-Recall curve')
    plt.axhline(y=auc_precision_recall, color='r', linestyle='--', label=f'Avg Precision: {auc_precision_recall:.4f}')
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Precision-Recall Curve')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_filename)

    # print(f"overlapping nodes: {len(set(node_df_merged['Node'].tolist()) & gold_standard_nodes)}")
    # print(f"average_precision_score: {auc_precision_recall}")

# TODO: fix mincostflow bug with summarize networks
algorithms = ['mincostflow', 'omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'allpairs', 'domino']

gold_standard_file = "output/gs_egfr-merged.pickle"
node_table = Evaluation.from_file(gold_standard_file).node_table
new_folder_path = 'parameter-tuning/ensembling-parameter-tuning/'

for algo in algorithms:
    ensemble_filename = f"output/tps_egfr-ml/{algo}-ensemble-pathway.txt"
    node_freq_filename = f"{new_folder_path}{algo}-frequencies.txt"
    output_filename = f"{new_folder_path}{algo}-pr.png"
    try:
        precision_recall(ensemble_filename, node_table, node_freq_filename, output_filename)
    except Exception as error:
        print(error)

# code to work for MEO
algorithms = ['meo']

for algo in algorithms:
    ensemble_filename = f"output/tps_egfr-ml/{algo}-ensemble-pathway.txt"
    df = pd.read_table(ensemble_filename, sep="\t", header=0)
    df['Node1'] = df['Node1'] + '_HUMAN'
    df['Node2'] = df['Node2'] + '_HUMAN'
    df['Node1'] = df['Node1'].replace({
    'Ca++_HUMAN': 'Ca++_PSEUDONODE',
    'PI3,4,5P3_HUMAN': 'PI3,4,5P3_PSEUDONODE',
    'DAG_HUMAN': 'DAG_PSEUDONODE'
    })
    df['Node2'] = df['Node2'].replace({
    'Ca++_HUMAN': 'Ca++_PSEUDONODE',
    'PI3,4,5P3_HUMAN': 'PI3,4,5P3_PSEUDONODE',
    'DAG_HUMAN': 'DAG_PSEUDONODE'
    })

    updated_ensemble_filename = f"{new_folder_path}meo-ensemble-pathway-updated.txt"
    df.to_csv(updated_ensemble_filename, sep="\t", header=True, index=False)
    node_freq_filename = f"{new_folder_path}{algo}-frequencies.txt"
    output_filename = f"{new_folder_path}{algo}-pr.png"
    try:
        precision_recall(updated_ensemble_filename, node_table, node_freq_filename, output_filename)
    except Exception as error:
        print(error)


#################################################################################################################################################
# No Parameter Tuning

def precision_and_recall(file_paths: Iterable[Path], node_table: pd.DataFrame, output_file: str):
    """
    Takes in file paths for a specific dataset and an associated gold standard node table.
    Calculates recall for each pathway file
    Returns output back to output_file
    @param file_paths: file paths of pathway reconstruction algorithm outputs
    @param node_table: the gold standard nodes
    @param output_file: the filename to save the precision of each pathway
    """
    y_true = set(node_table['NODEID'])
    results = []

    for file in file_paths:
        df = pd.read_table(file, sep="\t", header=0, usecols=["Node1", "Node2"])
        y_pred = set(df['Node1']).union(set(df['Node2']))
        all_nodes = y_true.union(y_pred)
        y_true_binary = [1 if node in y_true else 0 for node in all_nodes]
        y_pred_binary = [1 if node in y_pred else 0 for node in all_nodes]

        # default to 0.0 if there is a divide by 0 error
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0.0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0.0)
        results.append({"Pathway": file, "Precision": precision, "Recall": recall})

    pr_df = pd.DataFrame(results)
    pr_df.sort_values(by=["Recall"], axis=0, ascending=True, inplace=True)
    pr_df.to_csv(output_file, sep="\t", index=False)
    return pr_df


algorithms = ['mincostflow', 'omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'allpairs', 'domino']

gold_standard_file = "output/gs_egfr-merged.pickle"
node_table = Evaluation.from_file(gold_standard_file).node_table
folder_path = 'output/'
new_folder_path = 'parameter-tuning/no-parameter-tuning/'

for algo in algorithms:
    file_pattern = os.path.join(folder_path, f"tps_egfr-{algo}-*", "pathway.txt")
    files = glob.glob(file_pattern)
    output_file = f"{new_folder_path}{algo}-precision-and-recall.txt"
    prcurve_filename = f"{new_folder_path}{algo}-precision-and-recall-curve.png"

    pr_df = precision_and_recall(file_paths=files, node_table=node_table, output_file=output_file)

    plt.figure(figsize=(8, 6))
    plt.plot(pr_df["Recall"], pr_df["Precision"], marker='o', linestyle='-', color='b', label="PR")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"{algo} Precision-Recall Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(prcurve_filename)


# code to work for MEO
def precision_and_recall_meo(file_paths: Iterable[Path], node_table: pd.DataFrame, output_file: str):
    """
    Takes in file paths for a specific dataset and an associated gold standard node table.
    Calculates recall for each pathway file
    Returns output back to output_file
    @param file_paths: file paths of pathway reconstruction algorithm outputs
    @param node_table: the gold standard nodes
    @param output_file: the filename to save the precision of each pathway
    """
    y_true = set(node_table['NODEID'])
    results = []

    for file in file_paths:
        df = pd.read_table(file, sep="\t", header=0, usecols=["Node1", "Node2"])
        df['Node1'] = df['Node1'] + '_HUMAN'
        df['Node2'] = df['Node2'] + '_HUMAN'
        df['Node1'] = df['Node1'].replace({
        'Ca++_HUMAN': 'Ca++_PSEUDONODE',
        'PI3,4,5P3_HUMAN': 'PI3,4,5P3_PSEUDONODE',
        'DAG_HUMAN': 'DAG_PSEUDONODE'
        })
        df['Node2'] = df['Node2'].replace({
        'Ca++_HUMAN': 'Ca++_PSEUDONODE',
        'PI3,4,5P3_HUMAN': 'PI3,4,5P3_PSEUDONODE',
        'DAG_HUMAN': 'DAG_PSEUDONODE'
        })

        y_pred = set(df['Node1']).union(set(df['Node2']))
        all_nodes = y_true.union(y_pred)
        y_true_binary = [1 if node in y_true else 0 for node in all_nodes]
        y_pred_binary = [1 if node in y_pred else 0 for node in all_nodes]

        # default to 0.0 if there is a divide by 0 error
        precision = precision_score(y_true_binary, y_pred_binary, zero_division=0.0)
        recall = recall_score(y_true_binary, y_pred_binary, zero_division=0.0)
        results.append({"Pathway": file, "Precision": precision, "Recall": recall})

    pr_df = pd.DataFrame(results)
    pr_df.sort_values(by=["Recall"], axis=0, ascending=True, inplace=True)
    pr_df.to_csv(output_file, sep="\t", index=False)
    return pr_df

algorithms = ['meo']

for algo in algorithms:

    file_pattern = os.path.join(folder_path, f"tps_egfr-{algo}-*", "pathway.txt")
    files = glob.glob(file_pattern)
    output_file = f"{new_folder_path}{algo}-precision-and-recall.txt"
    prcurve_filename = f"{new_folder_path}{algo}-precision-and-recall-curve.png"

    pr_df = precision_and_recall_meo(file_paths=files, node_table=node_table, output_file=output_file)

    plt.figure(figsize=(8, 6))
    plt.plot(pr_df["Recall"], pr_df["Precision"], marker='o', linestyle='-', color='b', label="PR")
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title(f"{algo} Precision-Recall Curve")
    plt.legend()
    plt.grid(True)
    plt.savefig(prcurve_filename)

#################################################################################################################################################
# PCA parameter tuning

algorithms = ['omicsintegrator1', 'omicsintegrator2', 'pathlinker', 'domino', 'meo', 'allpairs']
folder_path = 'output/'
gold_standard_file = "output/gs_egfr-merged.pickle"
node_table = Evaluation.from_file(gold_standard_file).node_table
new_folder_path = 'parameter-tuning/pca-parameter-tuning/'

for algo in algorithms:
    file_path = os.path.join(folder_path, f"tps_egfr-ml", f"{algo}-pca-coordinates.txt")
    try:
        coord_df = pd.read_csv(file_path, delimiter="\t", header=0)
    except Exception as error:
        print(f"PCA parameter tuning: {error}")
        continue

    # centroid 
    centroid_row = coord_df[coord_df['algorithm'] == 'centroid']
    centroid = centroid_row.iloc[0, 1:].tolist()

    # update df to exclude centroid point
    coord_df = coord_df[coord_df['algorithm'] != 'centroid']

    # euclidean distance
    pc_columns = [col for col in coord_df.columns if col.startswith('PC')]
    coord_df['Distance To Centroid'] = np.sqrt(sum((coord_df[pc] - centroid[i]) ** 2 for i, pc in enumerate(pc_columns)))
    closest_to_centroid = coord_df.sort_values(by='Distance To Centroid').iloc[0]
    
    # finding the rep pathway
    rep_pathway = [os.path.join(folder_path, f"{closest_to_centroid['algorithm']}", "pathway.txt")]
    output_file = f"{new_folder_path}{algo}-precision-and-recall.txt"
    precision_and_recall(rep_pathway, node_table, output_file)
