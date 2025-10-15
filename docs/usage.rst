Using SPRAS
===========

SPRAS is run through `Snakemake <https://snakemake.readthedocs.io/>`_, which comes
with both the SPRAS conda environment and as a dependency of SPRAS.

To run SPRAS, run the following command inside the ``spras`` directory,
specifying a ``config.yaml`` and the number of cores to run SPRAS with:

.. code-block:: bash

    spras run --cores 1 --configfile config.yaml

Parallelizing SPRAS
-------------------

SPRAS works on any specified number of cores, and will, thanks to Snakemake,
automatically know how to best distribute work across various cores to
finish work specified in a configuration as fast as
possible.

To parallelize SPRAS, specify ``--cores`` to be a value higher than ``1``:

.. code-block:: bash

    spras run --cores 4 --configfile config.yaml

SPRAS also supports high-performance computing with it's integration with
`HTCondor <https://htcondor.org/>`_. See :doc:`Running with HTCondor <../htcondor>`
for more information.
