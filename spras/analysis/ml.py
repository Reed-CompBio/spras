from os import PathLike
from pathlib import PurePath
from typing import Iterable, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from adjustText import adjust_text
from scipy.cluster.hierarchy import dendrogram, fcluster
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from spras.util import make_required_dirs

plt.switch_backend('Agg')

linkage_methods = ["ward", "complete", "average", "single"]
distance_metrics = ["euclidean", "manhattan", "cosine"]

UNDIR_CONST = '---'  # separator between nodes when forming undirected edges
DIR_CONST = '-->'  # separator between nodes when forming directed edges
DPI = 300


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
                parts = line.split('\t')
                if len(parts) > 0:  # in case of empty line in file
                    node1 = parts[0]
                    node2 = parts[1]
                    direction = str(parts[3]).strip()
                    if direction == "U":
                        # node order does not matter, sort nodes so they can be matched across pathways
                        edges.append(UNDIR_CONST.join(sorted([node1, node2])))
                    elif direction == "D":
                        # node order does matter for directed edges
                        edges.append(DIR_CONST.join([node1, node2]))
                    else:
                        ValueError(f"direction is {direction}, rather than U or D")

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

def create_palette(column_names):
    """
    Generates a dictionary mapping each column name (algorithm name)
    to a unique color from the specified palette.
    """
    # TODO: could add a way for the user to customize the color palette?
    custom_palette = sns.color_palette("husl", len(column_names))
    label_color_map = {label: color for label, color in zip(column_names, custom_palette)}
    return label_color_map


def pca(dataframe: pd.DataFrame, output_png: str, output_var: str, output_coord: str, components: int = 2, labels: bool = True):
    """
    Performs PCA on the data and creates a scatterplot of the top two principal components.
    It saves the plot, the variance explained by each component, and the
    coordinates corresponding to the plot of each algorithm in a separate file.
    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_png: the filename to save the scatterplot
    @param output_var: the filename to save the variance explained by each component
    @param output_coord: the filename to save the coordinates of each algorithm
    @param components: the number of principal components to calculate (Default is 2)
    @param labels: determines if labels will be included in the scatterplot (Default is True)
    """
    df = dataframe.reset_index(drop=True)
    columns = dataframe.columns
    column_names = [element.split('-')[-3] for element in columns]  # assume algorithm names do not contain '-'
    df = df.transpose()  # based on the algorithms rather than the edges
    X = df.values

    min_shape = min(df.shape)
    if components < 2:
        raise ValueError(f"components={components} must be greater than or equal to 2 in the config file.")
    elif components > min_shape:
        print(f"components={components} is not valid. Setting components to {min_shape}.")
        components = min_shape
    if not isinstance(labels, bool):
        raise ValueError(f"labels={labels} must be True or False")

    scaler = StandardScaler()
    scaler.fit(X)  # calc mean and standard deviation
    X_scaled = scaler.transform(X)

    # choosing the PCA
    pca_instance = PCA(n_components=components)
    pca_instance.fit(X_scaled)
    X_pca = pca_instance.transform(X_scaled)
    variance = pca_instance.explained_variance_ratio_ * 100

    # making the plot
    label_color_map = create_palette(column_names)
    plt.figure(figsize=(10, 7))
    sns.scatterplot(x=X_pca[:, 0], y=X_pca[:, 1], s=70, hue=column_names, legend=True, palette=label_color_map)
    plt.title("PCA")
    plt.xlabel(f"PC1 ({variance[0]:.1f}% variance)")
    plt.ylabel(f"PC2 ({variance[1]:.1f}% variance)")

    # saving the coordinates of each algorithm
    make_required_dirs(output_coord)
    coordinates_df = pd.DataFrame(X_pca, columns = ['PC' + str(i) for i in range(1, components+1)])
    coordinates_df.insert(0, 'algorithm', columns.tolist())
    coordinates_df.to_csv(output_coord, sep='\t', index=False)

    # saving the principal components
    make_required_dirs(output_var)
    with open(output_var, "w") as f:
        for component in range(len(variance)):
            f.write("PC%d: %s\n" % (component+1, variance[component]))

    # labeling the graphs
    if labels:
        x_coord = coordinates_df['PC1'].to_numpy()
        y_coord = coordinates_df['PC2'].to_numpy()
        texts = []
        for i, algorithm in enumerate(column_names):
            texts.append(plt.text(x_coord[i], y_coord[i], algorithm, size=10))
        adjust_text(texts, force_points=(5.0, 5.0), arrowprops=dict(arrowstyle='->', color='black'))

    # saving the PCA plot
    make_required_dirs(output_png)
    plt.savefig(output_png, dpi=DPI)


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


def hac_vertical(dataframe: pd.DataFrame, output_png: str, output_file: str, linkage: str = 'ward', metric: str = 'euclidean'):
    """
    Performs hierarchical agglomerative clustering on the dataframe,
    creates a dendrogram of the resulting tree using seaborn and scipy for the cluster groups,
    and saves the dendrogram and the cluster labels of said dendrogram in separate files.
    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_png: the file name to save the dendrogram image
    @param output_file: the file name to save the clustering labels
    @param linkage: methods for calculating the distance between clusters
    @param metric: used for distance computation between instances of clusters
    """
    if linkage not in linkage_methods:
        raise ValueError(f"linkage={linkage} must be one of {linkage_methods}")
    if metric not in distance_metrics:
        raise ValueError(f"metric={metric} must be one of {distance_metrics}")
    if metric == "manhattan":
        # clustermap does not support manhattan as a metric but cityblock is equivalent per
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.pdist.html#scipy.spatial.distance.pdist
        metric = "cityblock"
    if linkage == "ward":
        if metric != "euclidean":
            print("For linkage='ward', the metric must be 'euclidean'; setting metric = 'euclidean")
            metric = "euclidean"

    df = dataframe.reset_index(drop=True)
    columns = df.columns
    column_names = [element.split('-')[-3] for element in columns]  # assume algorithm names do not contain '-'
    df = df.transpose()

    # create a color map for the given labels
    # and map it to the dataframe's index for row coloring in the plot
    label_color_map = create_palette(column_names)
    row_colors = pd.Series(column_names, index=df.index).map(label_color_map)

    # plotting the seaborn figure
    plt.figure(figsize=(10, 7))
    clustergrid = sns.clustermap(df, metric=metric, method=linkage, row_colors=row_colors, col_cluster=False)
    clustergrid.ax_heatmap.remove()
    clustergrid.cax.remove()
    clustergrid.ax_row_dendrogram.set_visible(True)
    clustergrid.ax_col_dendrogram.set_visible(False)
    legend_labels = [plt.Rectangle((0, 0), 0, 0, color=label_color_map[label]) for label in label_color_map]
    plt.legend(legend_labels, label_color_map.keys(), bbox_to_anchor=(1.02, 1), loc='upper left')

    # Use linkage matrix from seaborn clustergrid to generate cluster assignments
    # then using fcluster with a distance thershold(t) to make the clusters
    linkage_matrix = clustergrid.dendrogram_row.linkage
    clusters = fcluster(linkage_matrix, t=0.5, criterion='distance')
    cluster_data = {'algorithm': columns.tolist(), 'labels': clusters}
    clusters_df = pd.DataFrame(cluster_data)

    # saving files
    make_required_dirs(output_file)
    clusters_df.to_csv(output_file, sep='\t', index=False)
    make_required_dirs(output_png)
    plt.savefig(output_png, bbox_inches="tight", dpi=DPI)


def hac_horizontal(dataframe: pd.DataFrame, output_png: str, output_file: str, linkage: str = 'ward', metric: str = 'euclidean'):
    """
    Performs hierarchical agglomerative clustering on the dataframe,
    creates a dendrogram of the resulting tree using sckit learn and makes cluster groups scipy,
    and saves the dendrogram and the cluster labels of said dendrogram in separate files.
    @param dataframe: binary dataframe of edge comparison between algorithms from summarize_networks
    @param output_png: the file name to save the dendrogram image
    @param output_file: the file name to save the clustering labels
    @param linkage: methods for calculating the distance between clusters
    @param metric: used for distance computation between instances of clusters
    """
    if linkage not in linkage_methods:
        raise ValueError(f"linkage={linkage} must be one of {linkage_methods}")
    if linkage == "ward":
        if metric != "euclidean":
            print("For linkage='ward', the metric must be 'euclidean'; setting metric = 'euclidean")
            metric = "euclidean"
    if metric not in distance_metrics:
        raise ValueError(f"metric={metric} must be one of {distance_metrics}")

    df = dataframe.reset_index(drop=True)
    df = df.transpose()

    # plotting figure
    plt.figure(figsize=(10, 7))
    model = AgglomerativeClustering(linkage=linkage, affinity=metric,distance_threshold=0.5, n_clusters=None)
    model = model.fit(df)
    plt.figure(figsize=(10, 7))
    plt.title("Hierarchical Agglomerative Clustering Dendrogram")
    plt.xlabel("algorithms")
    algo_names = list(dataframe.columns)
    plot_dendrogram(model, labels=algo_names, leaf_rotation=90, leaf_font_size=10, color_threshold=0,
                    truncate_mode=None)

    # saving cluster assignments
    cluster_data = {'algorithm': algo_names, 'labels': model.labels_}
    clusters_df = pd.DataFrame(cluster_data)

    # saving files
    make_required_dirs(output_file)
    clusters_df.to_csv(output_file, sep='\t', index=False)
    make_required_dirs(output_png)
    plt.savefig(output_png, bbox_inches="tight", dpi=DPI)


def ensemble_network(dataframe: pd.DataFrame, output_file: str):
    """
    Calculates the mean of the binary values in the provided dataframe to create an ensemble pathway.
    Counts the number of times an edge appears in a set of pathways and divides by the total number of pathways.
    Edges that appear more frequently across pathways are more likely to be robust,
    so this information can be used to filter edges in a final network.
    @param dataframe: binary dataframe of edge presence and absence in each pathway from summarize_networks
    @param output_file: the filename to save the ensemble network
    """
    row_means = dataframe.mean(axis=1, numeric_only=True).reset_index()
    row_means.columns = ['Edges', 'Frequency']

    # Add a 'Direction' column, set to 'D' if edge is directed ('-->'), else 'U'
    row_means['Direction'] = row_means['Edges'].apply(lambda edge: 'D' if DIR_CONST in edge else 'U')

    # Extracts the start node connected from "---" or "-->" from column Edges and adds the start node to column Node2
    row_means['Node1'] = row_means['Edges'].apply(
        lambda edge: edge.split(DIR_CONST)[0] if DIR_CONST in edge else edge.split(UNDIR_CONST)[0])

    # Extracts the end node connected from "---" or "-->" from column Edges and adds the end node to column Node2
    row_means['Node2'] = row_means['Edges'].apply(
        lambda edge: edge.split(DIR_CONST)[1] if DIR_CONST in edge else edge.split(UNDIR_CONST)[1])

    make_required_dirs(output_file)
    row_means[['Node1', 'Node2', 'Frequency', "Direction"]].to_csv(output_file, sep='\t', index=False, header=True)
