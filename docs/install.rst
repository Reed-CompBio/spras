##################
 Installing SPRAS
##################

SPRAS provides several convenient ways to use the package, depending on
your needs

************
 Using Pixi
************

If you want to run spras locally on your machine, you can use the
provided `pyproject.toml` file to create a `pixi` environment with all
the necessary dependencies: 1. `Download and Install Pixi`_ 2. Activate
the pixi environment:

.. code:: bash

   pixi shell

*****************************
 Installing SPRAS with `pip`
*****************************

You can also install SPRAS as a package using `pip` directly from the
github repository:

.. code:: bash

   pip install git+https://github.com/Reed-CompBio/spras.git

********************************
 Getting the SPRAS Docker Image
********************************

SPRAS also publishes a Docker image that already holds all the necessary
dependencies. Assuming you have Docker installed, you can pull the image
from Docker Hub:

.. code:: bash

   docker pull reedcompbio/spras:latest

If you want to pull a specific version of spras, use the version for the
image tag name. For example, to get spras v0.6.0:

.. code:: bash

   docker pull reedcompbio/spras:0.6.0

.. _download and install pixi: https://pixi.sh/latest/installation/
