# Datasets
This directory contains example datasets.
It can also be used to store new input data files.
There are currently very small toy datasets and one real dataset.

For information about file formats, see the
[file format documentation](https://spras.readthedocs.io/en/latest/output.html).

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

### EGFR Gold Standard

This EGFR gold standard nodes were prepared by downloading the EGFR reference node dataset from the Gitter Lab fork of the TPS repository: [EGFR Node File](https://github.com/gitter-lab/tps/blob/ca7cafd1e1c17f45ddea07c3fb54d0d70b86ff45/data/resources/eight-egfr-reference-all.txt).

We filtered the dataset by removing all nodes with the _PSEUDONODE suffix to focus only on biologically meaningful interactions.

This work is part of our ongoing effort to integrate an EGFR-specific gold standard into SPRAS, as discussed in issue [#178](https://github.com/Reed-CompBio/spras/issues/178).
