Using SPRAS
===========

SPRAS is run through `Snakemake <https://snakemake.readthedocs.io/>`_, which comes
with the SPRAS conda environment.

To run SPRAS, run the following command inside the ``spras`` directory,
specifying a ``config.yaml`` and the number of cores to run SPRAS with:

.. code-block:: bash

    snakemake --cores 1 --configfile config.yaml
