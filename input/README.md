# Datasets
This directory contains example datasets.
It can also be used to store new input data files.
There are currently very small toy datasets and one real dataset.

## File formats
### Node file
Node files include a header row and rows providing attributes for each node.
One column is for the node identifier and must have the header value `NODEID`.
All other columns specify additional node attributes such as prizes.
Any nodes that are listed in a node file but are not present in one or more edges in the edge file will be removed.
For example:
```
NODEID	prize	sources	targets	active
A	1.0		True	True
B	3.3	True		True
C	2.5		True	True
D	1.9	True	True	True
```

A secondary format provides only a list of node identifiers and uses the filename as the node attribute, as in the example `sources.txt`.
This format may be deprecated.

### Edge file
Edge files do not include a header row.
Each row lists the two nodes that are connected with an edge, the weight for that edge, and, optionally, a directionality column to indicate whether the edge is directed or undirected.
The directionality values are either a 'U' for an undirected edge or a 'D' for a directed edge.
If the directionality column is not included, SPRAS will assume that the file's edges are entirely undirected.
The weights are typically in the range [0,1] with 1 being the highest confidence for the edge.

For example:
```
A	B	0.98    U
B	C	0.77    D
```
or
```
A	B	0.98
B	C	0.77 
```

## Toy datasets
The following files are very small toy datasets used to illustrate the supported file formats
- `alternative-network.txt`
- `alternative-targets.txt`
- `network.txt`
- `node-prizes.txt`
- `sources.txt`
- `targets.txt`

## Epidermal growth factor receptor (EGFR)
This dataset represents protein phosphorylation changes in response to epidermal growth factor (EGF) treatment.
The network includes protein-protein interactions from [iRefIndex](http://irefindex.org/) and kinase-substrate interactions from [PhosphoSitePlus](http://www.phosphosite.org/).
The files are originally from the [Temporal Pathway Synthesizer (TPS)](https://github.com/koksal/tps) repository.
They have been lightly modified for SPRAS by lowering one edge weight that was greater than 1, removing 182 self-edges, removing a PSEUDONODE prize, and adding a prize of 10.0 to EGF_HUMAN.
The only source is EGF_HUMAN.
All proteins with phosphorylation-based prizes are also labeled as targets.
All nodes are considered active.

If you use any of the input files `tps-egfr-prizes.txt` or `phosphosite-irefindex13.0-uniprot.txt`, reference the publication

[Synthesizing Signaling Pathways from Temporal Phosphoproteomic Data](https://doi.org/10.1016/j.celrep.2018.08.085).
Ali Sinan Köksal, Kirsten Beck, Dylan R. Cronin, Aaron McKenna, Nathan D. Camp, Saurabh Srivastava, Matthew E. MacGilvray, Rastislav Bodík, Alejandro Wolf-Yadlin, Ernest Fraenkel, Jasmin Fisher, Anthony Gitter.
*Cell Reports* 24(13):3607-3618 2018.

If you use the network file `phosphosite-irefindex13.0-uniprot.txt`, also reference iRefIndex and PhosphoSitePlus.

[iRefIndex: a consolidated protein interaction database with provenance](https://doi.org/10.1186/1471-2105-9-405).
Sabry Razick, George Magklaras, Ian M Donaldson.
*BMC Bioinformatics* 9(405) 2008.

[PhosphoSitePlus, 2014: mutations, PTMs and recalibrations](https://doi.org/10.1093/nar/gku1267).
Peter V Hornbeck, Bin Zhang, Beth Murray, Jon M Kornhauser, Vaughan Latham, Elzbieta Skrzypek.
*Nucleic Acids Research* 43(D1):D512-520 2015.

The TPS [publication](https://doi.org/10.1016/j.celrep.2018.08.085) describes how the network data and protein prizes were prepared.

