import pandas as pd
from typing import Iterable
from pathlib import Path, PurePath
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import seaborn as sns
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram
import numpy as np
plt.switch_backend('Agg')


def summarize_networks(file_paths: Iterable[Path]) -> pd.DataFrame:
    '''
    will take in a list of filepaths and creates a binary dataframe where each 
    row corresponds to an edge and each column corresponds to an algorithm. 
    The values in the dataframe are 1 if the edge is present in 
    the algorithm and 0 otherwise.
    @param file_paths: file paths of algorithm outputs 
    '''
    # creating a tuple that contains the algorithm column name and edge pairs
    edge_tuples = []
    
    for file in file_paths:
        try:
           # collecting and sorting the edge pairs per algortihm
            with open(file,'r') as f:
                lines = f.readlines()
            
            edge = []
            for line in lines: 
                parts = line.split()
                if (len(parts) > 0): # incase of empty line in file
                    node1 = parts[0]
                    node2 = parts[1]
                    edge.append(''.join(sorted([node1, node2])))
           
            # getting the algorithm name
            p = PurePath(file)
            edge_tuples.append((p.parts[-2], edge))
            
        except FileNotFoundError:
            print(file, 'not found during ML analysis') # should hopefully not hit
            continue
        
    # the dataframes per algorithm
    edge_dataframes = []
    
    # the data frame is set up per algorithm and a 1 is set for the edge pair that exists in the algorithm
    for tuple in edge_tuples:

        dataframe = pd.DataFrame(
            {
                str(tuple[0]): 1,
            }, index= tuple[1]
        )
        edge_dataframes.append(dataframe)

    # concating all the data frames together (0 is set for all the edge pairs that don't exist per algorithm)
    concated_df = pd.concat(edge_dataframes, axis= 1, join = 'outer')
    concated_df = concated_df.fillna(0) 
    concated_df = concated_df.astype('int64')
    
    return concated_df


def pca(dataframe: pd.DataFrame, output_png: str, output_file: str, output_coord: str):

    '''
    performs PCA on the data and creates a scatterplot of the top two principal components. 
    It saves the plot, the variance of each component, and the 
    coordinates corresponding to the plot of each algorithm in a separate file.
    @param dataframe: binary dataframe of edge comparison between algorithms
    @param output_png: the filename to save the scatterplot 
    @param output_file: the filename to save the variance explained by each component
    @param output_coord: the filename to save the coordinates of each algorithm

    '''
    df = dataframe.reset_index(drop=True)
    df = df.transpose() #based on the algortihms rather than the edges 
    X = df.values

    scaler = StandardScaler()
    scaler.fit(X) # calc mean and standard deviation 
    X_scaled = scaler.transform(X)

    # chosing the PCA
    pca_2 = PCA(n_components=2)
    pca_2.fit(X_scaled)
    X_pca_2 = pca_2.transform(X_scaled)
    variance = pca_2.explained_variance_ratio_ *100
    
    # making the plot
    plt.figure(figsize = (10,7))
    # sns.set(font_scale = 1.5)
    sns.scatterplot(x = X_pca_2[:,0], y = X_pca_2[:,1], s = 70)
    plt.title("PCA")
    plt.xlabel(f"PC1 ({variance[0]:.1f}% variance)")
    plt.ylabel(f"PC2 ({variance[1]:.1f}% variance)")
    
    # saving the pca plot
    plt.savefig(output_png)

    # saving the principal components
    with open(output_file, "w") as f: 
        for component in variance:
            f.write("%s\n" % component)

    # saving the coordinates of each algorithm
    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'x': X_pca_2[:, 0], 'y': X_pca_2[:, 1]}
    df = pd.DataFrame(data)
    df.to_csv(output_coord, sep='\t', index=False)
   
# This function is taken from the scikit-learn version 1.2.1 example code
# https://scikit-learn.org/stable/auto_examples/cluster/plot_agglomerative_dendrogram.html
# available under the BSD 3-Clause License, Copyright 2007 - 2023, scikit-learn developers
def plot_dendrogram(model, **kwargs):
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


def hac(dataframe: pd.DataFrame, output_png: str, output_file: str):
    '''
    performs hierarchical agglomerative clustering on the data, 
    creates a dendrogram of the resulting tree, 
    and saves the dendrogram and the cluster labels of said dendrogram in separate files.
    @param dataframe: binary dataframe of edge comparison between algorithms
    @param output_png: the file name to save the dendrogram
    @param output_file: the file name to save the clustering labels
    '''

    X = dataframe.reset_index(drop=True)
    X = X.transpose()
    model = AgglomerativeClustering(distance_threshold = 0.5, n_clusters= None) # n_clusters = 2 and distance_threshold = None
    model = model.fit(X)

    plt.figure(figsize=(10,7))
    plt.title("Hierarchical Agglomerative Clustering Dendrogram")
    algo_names = list(dataframe.columns)
    plot_dendrogram(model, labels=algo_names, leaf_rotation=90, leaf_font_size=10, color_threshold=0, truncate_mode=None)
    plt.xlabel("algorithms")
    plt.savefig(output_png, bbox_inches="tight")

    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'labels': model.labels_}
    df = pd.DataFrame(data)
    df.to_csv(output_file, sep='\t', index=False)
