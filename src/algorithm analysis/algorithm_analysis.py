import pandas as pd
from typing import Iterable
from pathlib import Path

from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import seaborn as sns

from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram
import numpy as np

import argparse

def summarize_networks(file_paths: Iterable[Path]) -> pd.DataFrame:

    # nw = nx.read_weighted_edgelist(file_path) (already tested and works with spras) 
    # vs my parser (is my parser compatible with spras)

    edge_tuples = []
    
    for file in file_paths:
        with open(file,'r') as f:
            lines = [line[:3] for line in f.readlines()]
        
        line = []
        for char in lines:
            newChar = char.replace(' ','')
            line.append(newChar)
            
        e = [''.join(sorted(ele)) for ele in line]
        edge_tuples.append((file, e))

    edge_dataframes = []
    
    for tuple in edge_tuples:
        col_label = str(tuple[0])

        dataframe = pd.DataFrame(
            {
                col_label: 1,
            }, index= tuple[1]
        )
        edge_dataframes.append(dataframe)

    concated_df = pd.concat(edge_dataframes, axis= 1, join = 'outer')
    concated_df = concated_df.fillna(0) 
    concated_df = concated_df.astype('int64')
   
    return concated_df
    
def pca(dataframe: pd.DataFrame, output_png: str, output_file: str):

    df = dataframe.reset_index(drop=True)
    df = df.transpose() #based on the algortihms rather than the edges 
    X = df.values

    # standardize the df because if not in the same scale (rn it is 4,7)
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
    sns.scatterplot(x = X_pca_2[:,0], y = X_pca_2[:,1], s = 70, palette  = ['pink', 'blue'])
    plt.title("PCA")
    plt.xlabel("pc1 (" + str(variance[0]) +")")
    plt.ylabel("pc2 (" + str(variance[1]) +")")
    
    # saving the pca plot
    plt.savefig(output_png)

    # saving the principal components
    f = open(output_file, "w")
    f.write(str(variance))
    f.close()
    # error checking?
   
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
    dendrogram (linkage_matrix, **kwargs)

def hac(dataframe: pd.DataFrame, output_png: str):
    # turn the result returned prior into a csv file

    X = dataframe.reset_index(drop=True)
    X = X.transpose()
    model = AgglomerativeClustering(linkage='complete', distance_threshold=0, n_clusters=None)
    model = model.fit(X)

    plt.figure(figsize = (10,7))
    plt.title("Algorithm HAC Dendrogram")
    algo_names = list(dataframe.columns)
    plot_dendrogram(model, truncate_mode="level", p=3, labels=algo_names)
    plt.xlabel("algorithms")
    plt.savefig(output_png)

    
def main(args):
    
    dataframe = summarize_networks(args.edge_files)
    pca(dataframe, 'pca_image.png', 'pca_components.txt')
    hac(dataframe, 'hac_image.png')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
  
    parser.add_argument('--edge_files',
                        nargs='+',
                        type = str, 
                        required=True)
    
    # python algorithm_analysis.py --edge_files s1.txt /Users/nehatalluri/Desktop/jobs/research/spras/output/data0-mincostflow-params-SZPZVU6/pathway.txt
    
    args = parser.parse_args()

main(args)