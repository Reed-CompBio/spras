import pandas as pd
from matplotlib import pyplot as plt
from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram
import numpy as np


# from the docs
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



X = pd.read_csv('concatdf.csv')
X = X.transpose()
model = AgglomerativeClustering(linkage='complete', distance_threshold=0, n_clusters=None)
model = model.fit(X)

column_names = list(X.index)
print(column_names)

plt.title("Algorithm HAC Dendrogram")

# plot the top three levels of the dendrogram
plot_dendrogram(model, truncate_mode="level", p=3, labels=column_names)

plt.xlabel("algorithms") # not the names of the algos at this moment 
plt.savefig("hac.png")

# label the leaf nodes at least 