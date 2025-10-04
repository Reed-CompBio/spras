Using SPRAS
===========

SPRAS is run through `Snakemake <https://snakemake.readthedocs.io/>`_, which comes
with both the SPRAS conda environment and as a dependency of SPRAS.

To run SPRAS, run the following command inside the ``spras`` directory,
specifying a ``config.yaml`` and the number of cores to run SPRAS with:

.. code-block:: bash

    spras run --cores 1 --configfile config.yaml
