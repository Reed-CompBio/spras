# Datasets
This directory contains example datasets.
It can also be used to store new input data files.
There are currently very small toy datasets and one real dataset.

## Toy datasets
The following files are very small toy datasets used to illustrate supported file formats
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
They have been lightly modified for SPRAS by lowering one edge weight that was greater than 1, removing a PSEUDONODE prize, and converting all edges to undirected edges.
All proteins with phosphorylation-based prizes are also labeled as targets.
The only source is EGF.

If you use any of these input files, reference the publication  
[Synthesizing Signaling Pathways from Temporal Phosphoproteomic Data](https://doi.org/10.1016/j.celrep.2018.08.085).
Ali Sinan Köksal, Kirsten Beck, Dylan R. Cronin, Aaron McKenna, Nathan D. Camp, Saurabh Srivastava, Matthew E. MacGilvray, Rastislav Bodík, Alejandro Wolf-Yadlin, Ernest Fraenkel, Jasmin Fisher, Anthony Gitter.
*Cell Reports* 24(13):3607-3618 2018.

If you use the network file `phosphosite-irefindex13.0-uniprot.txt`, also reference iRefIndex and PhosphoSitePlus.
The publication describes how the network data and protein prizes were prepared.
