from os import PathLike
from pathlib import PurePath
from typing import Iterable, Union
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.cluster.hierarchy import dendrogram
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from adjustText import adjust_text
from src.util import make_required_dirs

plt.switch_backend('Agg')

linkage_methods = ["ward", "complete", "average", "single"]
distance_metrics = ["euclidean", "l1", "l2", "manhattan", "cosine", "precomputed"]
NODE_SEP = '|||'  # separator between nodes when forming edges in the dataframe

def summarize_networks(file_paths: Iterable[Union[str, PathLike]]) -> pd.DataFrame:
    """
    Takes in a list of file paths and creates a binary dataframe where each
    row corresponds to an edge and each column corresponds to an algorithm.
    The values in the dataframe are 1 if the edge is present in
    the algorithm and 0 otherwise.
    Assumes edges are undirected.
    @param file_paths: file paths of pathway reconstruction algorithm outputs
    """
    # creating a tuple that contains the algorithm column name and edge pairs
    edge_tuples = []
    for file in file_paths:
        try:
            # collecting and sorting the edge pairs per algortihm
            with open(file, 'r') as f:
                lines = f.readlines()

            edges = []
            for line in lines:
                parts = line.split()
                if len(parts) > 0:  # in case of empty line in file
                    node1 = parts[0]
                    node2 = parts[1]
                    edges.append(NODE_SEP.join(sorted([node1, node2])))  # assumes edges are undirected

            # getting the algorithm name
            p = PurePath(file)
            edge_tuples.append((p.parts[-2], edges))

        except FileNotFoundError:
            print(file, ' not found during ML analysis')  # should not hit this
            continue

    # initially construct separate dataframes per algorithm
    edge_dataframes = []
    # the dataframe is set up per algorithm and a 1 is set for the edge pair that exists in the algorithm
    for tup in edge_tuples:
        dataframe = pd.DataFrame(
            {
                str(tup[0]): 1,
            }, index=tup[1]
        )
        edge_dataframes.append(dataframe)

    # concatenating all the algorithm-specific dataframes together
    # (0 is set for all the edge pairs that don't exist per algorithm)
    concated_df = pd.concat(edge_dataframes, axis=1, join='outer')
    concated_df = concated_df.fillna(0)
    concated_df = concated_df.astype('int64')

    return concated_df

def pca(dataframe: pd.DataFrame, output_png: str, output_file: str, output_coord: str, components=2, labels=True):
    """
    Performs PCA on the data and creates a scatterplot of the top two principal components.
    It saves the plot, the variance explained by each component, and the
    coordinates corresponding to the plot of each algorithm in a separate file.
    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_png: the filename to save the scatterplot
    @param output_file: the filename to save the variance explained by each component
    @param output_coord: the filename to save the coordinates of each algorithm
    """

    df = dataframe.reset_index(drop=True)
    column_names = df.head()
    column_names = [element.split('-')[1] for element in column_names]
    df = df.transpose()  # based on the algorithms rather than the edges
    X = df.values

    min_shape = min(df.shape)
    if components < 2:
        raise ValueError(f"components={components} must be greater than or equal to 2 in the config file.")
    elif components > min_shape:
        print(f"n_components={components} is not valid. Setting components to {min_shape}.")
        components = min_shape
    if not isinstance(labels, bool):
        raise ValueError(f"labels={labels} must be True or False")

    scaler = StandardScaler()
    scaler.fit(X)  # calc mean and standard deviation
    X_scaled = scaler.transform(X)

    # choosing the PCA
    pca = PCA(n_components=components)
    pca.fit(X_scaled)
    X_pca = pca.transform(X_scaled)
    variance = pca.explained_variance_ratio_ * 100

    # making the plot
    plt.figure(figsize=(10, 7))
    sns.scatterplot(x=X_pca[:, 0], y=X_pca[:, 1], s=70, hue=column_names, legend=True);
    plt.title("PCA")
    plt.xlabel(f"PC1 ({variance[0]:.1f}% variance)")
    plt.ylabel(f"PC2 ({variance[1]:.1f}% variance)")

    # saving the coordinates of each algorithm
    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'x': X_pca[:, 0], 'y': X_pca[:, 1]}
    df = pd.DataFrame(data)
    make_required_dirs(output_coord)
    df.to_csv(output_coord, sep='\t', index=False)

    # saving the principal components
    make_required_dirs(output_file)
    with open(output_file, "w") as f:
        for component in variance:
            f.write("%s\n" % component)

    # labeling the graphs
    if (labels):
        algorithm_names = df['algorithm'].to_numpy()
        algorithm_names = [element.split()[0].split('-')[1] for element in algorithm_names]
        x_coord = df['x'].to_numpy()
        y_coord = df['y'].to_numpy()

        texts = []
        for i, algorithm in enumerate(algorithm_names):
            # TODO: can add a threshold here to allow for labeled points
            texts.append(plt.text(x_coord[i], y_coord[i], algorithm, size=9))
        
        adjust_text(texts, force_points= [5,5], arrowprops=dict(arrowstyle='->', color='red'))

    # saving the PCA plot
    make_required_dirs(output_png)
    plt.savefig(output_png)
    

# This function is taken from the scikit-learn version 1.2.1 example code
# https://scikit-learn.org/stable/auto_examples/cluster/plot_agglomerative_dendrogram.html
# available under the BSD 3-Clause License, Copyright 2007 - 2023, scikit-learn developers
def plot_dendrogram(model, **kwargs):
    """
    Plot a dendrogram to visualize a hierarchical clustering solution
    @param model: the fit AgglomerativeClustering model
    @param kwargs: arguments passed to the dendrogram function
    """
    # Create linkage matrix and then plot the dendrogram

    # create the counts of samples under each node
    counts = np.zeros(model.children_.shape[0])
    n_samples = len(model.labels_)
    for i, merge in enumerate(model.children_):
        current_count = 0
        for child_idx in merge:
            if child_idx < n_samples:
                current_count += 1  # leaf node
            else:
                current_count += counts[child_idx - n_samples]
        counts[i] = current_count

    linkage_matrix = np.column_stack(
        [model.children_, model.distances_, counts]
    ).astype(float)

    # Plot the corresponding dendrogram
    dendrogram(linkage_matrix, **kwargs)

def hac_vertical(dataframe: pd.DataFrame, output_png: str, output_file: str, linkage='ward', metric='euclidean'):
    """
    Performs hierarchical agglomerative clustering on the dataframe,
    creates a dendrogram of the resulting tree USING SEABORN and SCKIT-LEARN for the cluster groups,
    and saves the dendrogram and the cluster labels of said dendrogram in separate files.
    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_png: the file name to save the dendrogram image
    @param output_file: the file name to save the clustering labels
    """

    if linkage not in linkage_methods:
        raise ValueError(f"linkage={linkage} must be one of {linkage_methods}")
    if linkage == "ward":
        if metric != "euclidean":
            print("For linkage='ward', the metric must be 'euclidean'; setting metric = 'euclidean")
            metric = "euclidean"
    if metric not in distance_metrics:
        raise ValueError(f"metric={metric} must be one of {distance_metrics}")
        
    X = dataframe.reset_index(drop=True)
    column_names = X.head()
    column_names = [element.split('-')[1] for element in column_names]
    X = X.transpose() 

    # creating the colors per algorithms
    custom_palette = sns.color_palette("tab10", len(column_names))
    label_color_map = {label: color for label, color in zip(column_names, custom_palette)}
    row_colors = pd.Series(column_names, index=X.index).map(label_color_map)

    #plotting the seaborn figure
    plt.figure(figsize=(10, 7))
    clustergrid = sns.clustermap(X, metric=metric, method=linkage, row_colors=row_colors, col_cluster=False)
    clustergrid.ax_heatmap.remove()
    clustergrid.cax.remove()
    clustergrid.ax_row_dendrogram.set_visible(True)
    clustergrid.ax_col_dendrogram.set_visible(False)
    legend_labels = [plt.Rectangle((0, 0), 0, 0, color=label_color_map[label]) for label in label_color_map]
    plt.legend(legend_labels, label_color_map.keys(), bbox_to_anchor=(1.02, 1), loc='upper left')
    
    make_required_dirs(output_png)
    plt.savefig(output_png, bbox_inches="tight")

    # getting the label of which group each algorithm combination falls under
    model = AgglomerativeClustering(linkage=linkage, affinity=metric,distance_threshold=0.5, n_clusters=None)
    model = model.fit(X)
    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'labels': model.labels_}
    df = pd.DataFrame(data)
    make_required_dirs(output_file)
    df.to_csv(output_file, sep='\t', index=False)


def hac_horizontal(dataframe: pd.DataFrame, output_png: str, output_file: str, linkage='ward', metric='euclidean'):
    """
    Performs hierarchical agglomerative clustering on the dataframe,
    creates a dendrogram of the resulting tree USING SCKIT LEARN and makes cluster groups USING SCKIT LEARN,
    and saves the dendrogram and the cluster labels of said dendrogram in separate files.
    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_png: the file name to save the dendrogram image
    @param output_file: the file name to save the clustering labels
    """

    if linkage not in linkage_methods:
        raise ValueError(f"linkage={linkage} must be one of {linkage_methods}")
    if linkage == "ward":
        if metric != "euclidean":
            print("For linkage='ward', the metric must be 'euclidean'; setting metric = 'euclidean")
            metric = "euclidean"
    if metric not in distance_metrics:
        raise ValueError(f"metric={metric} must be one of {distance_metrics}")
        
    X = dataframe.reset_index(drop=True)
    column_names = X.head()
    column_names = [element.split()[0].split('-')[1] for element in column_names]
    X = X.transpose() 
    
    plt.figure(figsize=(10, 7))
    model = AgglomerativeClustering(linkage=linkage, affinity=metric,distance_threshold=0.5, n_clusters=None)
    model = model.fit(X)
    plt.figure(figsize=(10, 7))
    plt.title("Hierarchical Agglomerative Clustering Dendrogram")
    plt.xlabel("algorithms")
    algo_names = list(dataframe.columns)
    plot_dendrogram(model, labels=algo_names, leaf_rotation=90, leaf_font_size=10, color_threshold=0,
                    truncate_mode=None)
    
    make_required_dirs(output_png)
    plt.savefig(output_png, bbox_inches="tight")

    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'labels': model.labels_}
    df = pd.DataFrame(data)
    make_required_dirs(output_file)
    df.to_csv(output_file, sep='\t', index=False)
