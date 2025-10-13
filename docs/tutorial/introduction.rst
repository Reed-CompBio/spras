##############
SPRAS Tutorial
##############

Purpose of this tutorial
========================
This tutorial will introduce participants to SPRAS and demonstrate how it can be used to explore biological pathways from omics data. 

Together, we will cover:

1. How to set up and run SPRAS
2. Running multiple algorithms with different parameters across one datasets
3. Using the post-analysis tools to evaluate and compare results
4. Building datasets for analysis
5. Other things you can do with SPRAS

Prerequisites for this tutorial
===============================
Required software:

- `Conda <https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html>`__ : for managing environments
- `Docker <https://www.docker.com/get-started/>`__ : for containerized runs
- `Cytoscape <https://cytoscape.org//>`__ for visualizing networks (download locally, the web version will not suffice)
- `Git <https://git-scm.com/downloads>`__: for cloning the SPRAS repository
- A terminal or code editor (`VS Code <https://code.visualstudio.com/download>`__ is recommended, but any terminal will work)

Required knowledge:

- Basic Python skills
- Basic biology concepts

###############
SPRAS Overview
###############

What is pathway reconstruction?
===============================
Pathway reconstruction is a computational approach used in biology to rebuild biological pathways (such as signaling pathways) from high-throughput experimental data.

Curated pathway databases provide references to pathways, but they are often generalized and may not capture the context-specific details relevant to a particular disease or experimental condition.
To address this, pathway reconstruction algorithms help map molecules of interest (such as proteins, genes, or metabolites identified in omics experiments or that are known as points of reference) onto large-scale interaction networks, called interactomes (maps of molecular interactions in a cell).
The result is a customized subnetwork (pathway) that reflects the biology of the specific experiment or condition.

Why use pathway reconstruction?
===============================
Pathway reconstruction algorithms allow researchers to systematically find context-specific subnetworks without performing exhaustive experiments. Different algorithms use distinct computational strategies and parameters, providing flexibility to highlight various aspects of the underlying biology and generate new, testable hypotheses giving researchers the flexibility to create and identify different subnetworks specific to their experimental conditions.

What is SPRAS?
===============
The Signaling Pathway Reconstruction Analysis Streamliner (SPRAS) is a computational framework that unifies, standardizes, and streamlines the use of diverse pathway reconstructon algorithms.

SPRAS provides an abstraction layer for pathway reconstruction algorithms by organizing every step into a unified schema. It uses workflow management (Snakemake), containerization, and config-driven runs to build modular and interoperable pipelines that cover the entire process:

1. Pre-processing of data
2. Algorithm execution
3. Post-processing of results
4. Downstream analysis and evaluation

A key strength of SPRAS is automation. From user provided input data and configurations, it can generate and execute complete workflows without requiring users to write complex scripts. This lowers the barrier to entry, allowing researchers to apply, evaluate, and compare multiple pathway reconstruction algorithms without deep computational expertise.

SPRAS also supports scalable, reproducible analyses, making it especially valuable for a large number datasets and systematic investigations. In addition, it provides built-in evaluation and post analysis tools that provide further insights of the algorithm outputs.