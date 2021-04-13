# Streamlining Signaling Pathway Reconstruction

This repo is a work-in-progress dockerized library of pathway reconstruction enhancement tools.
The framework will contain different graph algorithms that connect genes and proteins of interest in the context of a general protein-protein interaction network, allowing users to run multiple algorithms on their inputs.  To read more about the specific pathway reconstruction algorithms, refer to [our list of algorithms](https://github.com/Reed-CompBio/pathway-reconstruction-enhancer/tree/master/doc) within the `doc/` directory.
This library is inspired by tools for single-cell transcriptomics such as [BEELINE](https://github.com/Murali-group/Beeline) and [dynverse](https://github.com/dynverse) that provide a unified interface to many related algorithms.

Right now, this repo contains all the pieces that are being integrated into a single framework.
This is very much a work in progress.
The latest features can be found on various development branches.

## Components
**Configuration file**: Specifies which pathway reconstruction algorithms to run, which hyperparameter combinations to use, and which datasets to run them on.

**Snakemake file**: Defines a workflow to run all pathway reconstruction algorithms on all datasets with all specified hyperparameters.

**Dockerized pathway reconstruction algorithms**: Pathway reconstruction algorithms are run via Docker images using the docker-py Python package.
[PathLinker](https://github.com/Murali-group/PathLinker) is the first algorithm to prototype the workflow and design.

**Python wrapper for calling algorithms**: Wrapper functions provide an interface between the common file formats for input and output data and the algorithm-specific file formats and reconstruction commands.

Open a [GitHub issue](https://github.com/Reed-CompBio/pathway-reconstruction-enhancer/issues) or contact Anthony Gitter or Anna Ritz for more information.

## Docker
The `docker` subdirectory is not used by the main pathway reconstruction framework.
It serves as a reference for how to set up Dockerfiles and make Docker run calls.
