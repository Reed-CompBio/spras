import pandas as pd
from typing import Iterable
from pathlib import Path, PurePath
import os

import matplotlib.pyplot as plt
plt.switch_backend('Agg')
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import seaborn as sns

from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
import numpy as np

def summarize_networks(file_paths: Iterable[Path]) -> pd.DataFrame:

    # creating a tuple that contains the algorithm column name and edge pairs
    edge_tuples = []
    
    for file in file_paths:
        
        try:
           
           # collecting and sorting the edge pairs per algortihm
            with open(file,'r') as f:
                # under the assumption that it is single chars (maybe)
                # split on space char 
                # take the first and 0th elements and sort those 
                lines = [line[:3] for line in f.readlines()]
            
            line = []
            for char in lines:
                newChar = char.replace(' ','')
                line.append(newChar)
                
            # to deal with edges are the same but not ordered the same
            e = [''.join(sorted(ele)) for ele in line]

            
            # getting the algorithm name
            p = PurePath(file)
            edge_tuples.append((p.parts[-2], e))

  
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
        f.write(str(variance))

<<<<<<< HEAD
    # saving the coordinates of each algorithm
    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'x': X_pca_2[:, 0], 'y': X_pca_2[:, 1]}
    df = pd.DataFrame(data)
    df.to_csv(output_coord, sep='\t', index=False)
   
"""
@inproceedings{sklearn_api,
  author    = {Lars Buitinck and Gilles Louppe and Mathieu Blondel and
               Fabian Pedregosa and Andreas Mueller and Olivier Grisel and
               Vlad Niculae and Peter Prettenhofer and Alexandre Gramfort
               and Jaques Grobler and Robert Layton and Jake VanderPlas and
               Arnaud Joly and Brian Holt and Ga{\"{e}}l Varoquaux},
  title     = {{API} design for machine learning software: experiences from the scikit-learn
               project},
  booktitle = {ECML PKDD Workshop: Languages for Data Mining and Machine Learning},
  year      = {2013},
  pages = {108--122},
} 
"""
=======

# This function is taken from the scikit-learn version 1.2.1 example code
# https://scikit-learn.org/stable/auto_examples/cluster/plot_agglomerative_dendrogram.html
# available under the BSD 3-Clause License, Copyright 2007 - 2023, scikit-learn developers
>>>>>>> 7a975f62b473173f2963d9b46d0dff4344bf0acf
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

    X = dataframe.reset_index(drop=True)
    X = X.transpose()
    model = AgglomerativeClustering(distance_threshold = 0.5, n_clusters= None) # n_clusters = 2 and distance_threshold = None
    model = model.fit(X)

    # dist_matrix = squareform(model.distances_)
    # Z = linkage(np.reshape(model.distances_, (len(model.distances_), 1)), method='complete')
    # Z = linkage(model, method='complete')
    # Z = linkage(model.distances_, method='complete')

    # Z = linkage(model.children_, method= 'complete')

    # here for right now to make code work, but this may not be what we need to do
    plt.figure(figsize=(10,7))
    plt.title("Hierarchical Agglomerative Clustering Dendrogram")
    algo_names = list(dataframe.columns)
    plot_dendrogram(model, truncate_mode="level", p=3, labels=algo_names, leaf_rotation=90, leaf_font_size=10)
    # Z = linkage(model.children_, method= 'complete')
    # dendrogram(Z, leaf_font_size=10) #, labels=algo_names, leaf_rotation=90)

    plt.xlabel("algorithms")
    plt.savefig(output_png, bbox_inches="tight")
<<<<<<< HEAD


    columns = dataframe.columns.tolist()
    data = {'algorithm': columns, 'labels': model.labels_}
    df = pd.DataFrame(data)
    df.to_csv(output_file, sep='\t', index=False)
=======
>>>>>>> 7a975f62b473173f2963d9b46d0dff4344bf0acf
