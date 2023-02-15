import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from matplotlib import pyplot as plt
import seaborn as sns


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

plt.figure(figsize = (10,7))
sns.scatterplot(x = X_pca_2[:,0], y = X_pca_2[:,1], s = 70, palette  = ['pink', 'blue'])

print(pca_2.explained_variance_ratio_ *100)
plt.title("PCA")
plt.xlabel("principal component 1") # put the first component of explained variance
plt.ylabel("principal component 2")
plt.show()

#https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.annotate.html
# enumerate over the col header 