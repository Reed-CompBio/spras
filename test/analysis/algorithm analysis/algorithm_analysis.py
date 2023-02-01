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

    return concated_df 

# pass in file name to write the image and a second file name for a text file (anticpate this)
def pca(dataframe: pd.DataFrame):
    # turn the result returned prior into a csv file
    dataframe.to_csv('concatdf.csv',index=False)
    df = pd.read_csv('concatdf.csv')
    df = df.transpose() #based on the algortihms
    X = df.values
    print(X.shape)

    # standardize the df because if not in the same scale (rn it is 4,7)
    scaler = StandardScaler()
    scaler.fit(X) # calc mean and standard deviation 
    X_scaled = scaler.transform(X)


    # chosing the PCA
    pca_2 = PCA(n_components=2)
    pca_2.fit(X_scaled)
    X_pca_2 = pca_2.transform(X_scaled)

    fig = plt.figure(figsize = (10,7))
    sns.scatterplot(x = X_pca_2[:,0], y = X_pca_2[:,1], s = 70, palette  = ['pink', 'blue'])

    print(pca_2.explained_variance_ratio_ *100)
    plt.title("PCA")
    plt.xlabel("principal component 1") # put the first component of explained variance
    plt.ylabel("principal component 2")
    
    return fig

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

def hac(dataframe: pd.DataFrame):
    # turn the result returned prior into a csv file

    dataframe.to_csv('concatdf.csv',index=False)
    X = pd.read_csv('concatdf.csv')
    X = X.transpose()
    model = AgglomerativeClustering(linkage='complete', distance_threshold=0, n_clusters=None)
    model = model.fit(X)

    fig = plt.title("Algorithm HAC Dendrogram")

    # plot the top three levels of the dendrogram
    plot_dendrogram(model, truncate_mode="level", p=3)

    plt.xlabel("algorithms") # not the names of the algos at this moment 
    
    return fig



