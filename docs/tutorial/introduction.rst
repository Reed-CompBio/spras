COMBINE25 SPRAS Tutorial Introduction
======================================

What is pathway reconstruction?
-------------------------------------------------

.. Pathway reconstruction is a computational approach used in biology to rebuild biological pathways (such as signaling pathways) from high throughput experimental data.

.. Curated databases provide valuable references to pathways, but they are often generalized and may not capture the context-specific details relevant to a particular disease or experimental condition.
.. Pathway reconstruction addresses this limitation by mapping molecules of interest from omics data (these could be such as proteins, genes, or metabolites identified in omics experiments or that are interesting to look at) onto large-scale interaction networks (interactomes) (that are maps of molecular interactions in a cell) and finding ways to connect the molecules of interest. The result is a customized subnetwork that reflects the biology of the specific experiment.


Pathway reconstruction is a computational approach used in biology to rebuild biological pathways (such as signaling pathways) from high-throughput experimental data.

Curated pathway databases provide valuable references to pathways, but they are often generalized and may not capture the context-specific details relevant to a particular disease or experimental condition.
To address this, pathway reconstruction algorithms help map molecules of interest (such as proteins, genes, or metabolites identified in omics experiments or that are known as points of reference) onto large-scale interaction networks, called interactomes (maps of molecular interactions in a cell).
The result is a customized subnetwork (pathway) that reflects the biology of the specific experiment and condition.

Why use pathway reconstruction?
-------------------------------------------------

Pathway reconstruction algorithms allow researchers to systematically find context-specific subnetworks without performing exhaustive experiments. Different algorithms use distinct computational strategies and parameters, providing flexibility to highlight various aspects of the underlying biology and generate new, testable hypotheses giving researchers the flexibility to create and identify different subnetworks specific to their experimental conditions.

What is SPRAS?
-------------------------------------------------

The Signaling Pathway Reconstruction Analysis Streamliner (SPRAS) is a computational framework that unifies, standardizes, and streamlines the use of diverse pathway reconstructon algorithms (PRAs).

SPRAS provides an abstraction layer for PRAs by organizing every step into a unified schema. It uses workflow management (Snakemake), containerization, and config-driven runs to build modular and interoperable pipelines that cover the entire process:

1. Pre-processing of data
2. Algorithm execution
3. Post-processing of results
4. Downstream analysis and evaluation

A key strength of SPRAS is automation. From user provided input data and configurations, it can generate and execute complete workflows without requiring users to write complex scripts. This lowers the barrier to entry, allowing researchers to apply, evaluate, and compare multiple PRAs without deep computational expertise.

SPRAS also supports scalable, reproducible analyses, making it especially valuable for a large number datasets and systematic investigations. In addition, it provides built-in evaluation and post analysis tools that provide further insights of the algorithm outputs.


Purpose of this workshop
-------------------------------------------------

This workshop will introduce participants to SPRAS and demonstrate how it can be used to explore biological pathways from omics data. Together, we will cover:

1. How to set up and run SPRAS
2. Running multiple algorithms with different parameters across multiple datasets
3. Using the post-analysis tools to evaluate and compare results
4. Building datasets for analysis
5. Other things you can do with SPRAS (not fully shown/covered in this tutorial)

.. * i need to add in why it's important for this crowd
.. - the molecules/pathways found can be start points for further experimental processes that take these molecules as an start point for kinectics
.. - For the egfr dataset we throw away the time series data. With SPRAS we can't use time series data. For these people, spras's outputs can be key input proteins to look at for what their interested (like kinetics).

Prerequisites for this tutorial
-------------------------------------------------

Required software:

- Conda: for managing environments
- Docker: for containerized runs
- Cytoscape: for visualizing networks
- A terminal or code editor (VS Code is recommended, but any terminal will work)

Required knowledge:

- Basic Python skills
- Basic biology concepts
