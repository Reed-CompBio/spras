# Pathway Reconstruction Algorithms

The graph algorithms below have been used (or have the potential to be used) for the pathway reconstruction task. This task is typically formulated as follows: given a protein-protein interaction (PPI) network (represented as a graph, which may be weighted and/or directed) and a set of proteins of interest, return a subnetwork of the PPI graph that contains the proteins of interest.

## ANAT

**References:**
- Yosef et al. Toward accurate reconstruction of functional protein networks. _Molecular Systems Biology._ 2009. [doi:10.1038/msb.2009.3](https://www.embopress.org/doi/full/10.1038/msb.2009.3)
- Yosef et al. ANAT: a tool for constructing and analyzing functional protein networks. _Science Signaling._ 2011. [doi:10.1126/scisignal.2001935](https://doi.org/10.1126/scisignal.2001935)
- Almozlino et al. ANAT 2.0: reconstructing functional protein subnetworks. _BMC Bioinformatics._ 2017. [doi:10.1186/s12859-017-1932-1](https://dx.doi.org/10.1186%2Fs12859-017-1932-1)

## NetBox

**References:**
- Cerami et al. Automated network analysis identifies core pathways in glioblastoma. _PLoS One._ 2010. [doi:10.1371/journal.pone.0008918](https://dx.doi.org/10.1371%2Fjournal.pone.0008918)
- Liu et al. netboxr: Automated discovery of biological process modules by network analysis in R. _PLoS One._ 2020. [doi:10.1371/journal.pone.0234669](https://dx.doi.org/10.1371%2Fjournal.pone.0234669)

## ResponseNet

**References:**
- Yeger-Lotem et al. Bridging high-throughput genetic and transcriptional data reveals cellular responses to alpha-synuclein toxicity. _Nature Genetics._ 2009. [doi:10.1038/ng.337](https://dx.doi.org/10.1038%2Fng.337)
- Lan et al. ResponseNet: revealing signaling and regulatory networks linking genetic and transcriptomic screening data. _Nucleic Acids Research._ 2011. [doi:10.1093/nar/gkr359](https://dx.doi.org/10.1093%2Fnar%2Fgkr359)
- Basha et al., ResponseNet2.0: revealing signaling and regulatory pathways connecting your proteins and genes–now with human data. _Nucleic Acids Research._ 2013. [doi:10.1093/nar/gkt532](https://dx.doi.org/10.1093%2Fnar%2Fgkt532)
- Basha et al. ResponseNet v.3: revealing signaling and regulatory pathways connecting your proteins and genes across human tissues. _Nucleic Acids Research._ 2019. [doi:10.1093/nar/gkz421](https://dx.doi.org/10.1093%2Fnar%2Fgkz421)

## Prize Collecting Steiner Forest (PCSF): OmicsIntegrator1 and OmicsIntegrator2

**References:**
- Huang and Fraenkel. Integrating proteomic, transcriptional, and interactome data reveals hidden components of signaling and regulatory networks. _Science Signaling._ 2009. [doi:10.1126/scisignal.2000350](https://doi.org/10.1126/scisignal.2000350)
- Tuncbag et al. Simultaneous reconstruction of multiple signaling pathways via the prize-collecting steiner forest problem. _Journal of Computational Biology._ 2013. [doi:10.1089/cmb.2012.0092](https://doi.org/10.1089/cmb.2012.0092)
- Gitter et al. Sharing information to reconstruct patient-specific pathways in heterogeneous diseases.  _Pacific Symposium on Biocomputing._ 2014. [doi:10.1142/9789814583220_0005](https://doi.org/10.1142/9789814583220_0005)
- Tuncbag et al., Network-Based Interpretation of Diverse High-Throughput Datasets through the Omics Integrator Software Package. _PLoS Computational Biology._ 2016. [doi:10.1371/journal.pcbi.1004879](https://doi.org/10.1371/journal.pcbi.1004879)

One of the parameter options for OmicsIntegraor1 is `dummy_mode`.
There are 4 dummy mode possibilities:
 1. `terminals`: connect the dummy node to all nodes that have been assigned prizes
 2. `all`:  connect the dummy node to all nodes in the interactome i.e. full set of nodes in graph
 3. `others`: connect the dummy node to all nodes that are not terminal nodes i.e. nodes w/o prizes
 4. `file`: connect the dummy node to a specific list of nodes provided in a file
To support the `file` dummy node logic as part of OmicsIntegrator1, you can either add a separate `dummy.txt` file (and add this to the `node_files` argument in `config.yaml `) or add a `dummy` column node attribute to a file that contains `NODEID`, `prize`, `source`, etc.

## PathLinker

PathLinker takes as input (1) a weighted, directed PPI network, (2) two sets of nodes: a source set (representing receptors of a pathway of interest) and a target set (representing transcriptional regulators of a pathway of interest), and (3) an integer _k_. PathLinker efficiently computes the _k_-shortest paths from any source to any target and returns the subnetwork of the top _k_ paths as the pathway reconstruction.  Later work expanded PathLinker by incorporating protein localization information to re-score tied paths, dubbed Localized PathLinker (LocPL).

**References:**
- Ritz et al. Pathways on demand: automated reconstruction of human signaling networks.  _NPJ Systems Biology and Applications._ 2016. [doi:10.1038/npjsba.2016.2](https://doi.org/10.1038/npjsba.2016.2)
- Youssef, Law, and Ritz. Integrating protein localization with automated signaling pathway reconstruction. _BMC Bioinformatics._ 2019. [doi:10.1186/s12859-019-3077-x](https://doi.org/10.1186/s12859-019-3077-x)

## Pathway Reconstruction Augmenter (PRAUG)

**References:**
- Rubel and Ritz. Augmenting Signaling Pathway Reconstructions. _Proceedings of the 11th ACM International Conference on Bioinformatics, Computational Biology and Health Informatics (ACM-BCB '20)._ 2020. [doi:10.1145/3388440.3412411](https://doi.org/10.1145/3388440.3412411)

## Parameter Advising for Pathway Reconstruction Methods

**References:**
- Magnano and Gitter. Automating parameter selection to avoid implausible biological pathway models. _NPJ Systems Biology and Applications._ 2021. [doi:10.1038/s41540-020-00167-1](http://dx.doi.org/10.1038/s41540-020-00167-1)
