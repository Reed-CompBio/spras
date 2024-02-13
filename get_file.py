import requests
import pandas as pd

df = pd.read_csv('interactome-uniprot-collapsed-evidence.csv', sep='\t', header=0)
print(df.columns)
df.drop(columns=['#symbol1', 'symbol2', 'PubMedIDs', 'DBs', 'Evidence'], inplace=True)
print(df.head())
df['Rank'] = 1
print(df.head())
df['Direction'] = 'U'
print(df.head())
# Saving without headers
df.to_csv('interactome-uniprot-collapsed-evidence-network.txt', sep='\t', index=False, header=False)


