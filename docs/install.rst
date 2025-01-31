Installing SPRAS
================

SPRAS provides several convenient ways to use the package, depending on your needs

Using a Conda Environment
-------------------------
If you want to run spras locally on your machine, you can use the provided `environment.yml` file to create a conda environment
with all the necessary dependencies:
1. `Download and Install Conda`_
2. Build the `spras` conda environment and activate it:

.. code-block:: bash

    conda env create -f environment.yml
    conda activate spras

Installing SPRAS with `pip`
---------------------------
You can also install SPRAS as a package using `pip` directly from the github repository:

.. code-block:: bash

    pip install git+https://github.com/Reed-CompBio/spras.git

Getting the SPRAS Docker Image
----------------------------
SPRAS also publishes a Docker image that already holds all the necessary dependencies. Assuming you have Docker installed, you can pull
the image from Docker Hub:

.. code-block:: bash

    docker pull reedcompbio/spras:latest

If you want to pull a specific version of spras, use the version for the image tag name. For example, to get spras v0.2.0:

.. code-block:: bash

    docker pull reedcompbio/spras:0.2.0

.. _Download and Install Conda: https://conda-forge.org/download/