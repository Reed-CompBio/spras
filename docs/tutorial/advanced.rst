####################################
 Advanced Capabilities and Features
####################################

******************
 Parameter tuning
******************

Parameter tuning is the process of determining which parameter
combinations should be explored for each algorithm for a given dataset.
Parameter tuning focuses on defining and refining the parameter search
space.

Each dataset has unique characteristics so there are no preset
parameters combinations to use. Instead, we recommend tuning parameters
individually for each new dataset. SPRAS provides a flexible framework
for getting parameter grids for any algorithms for a given dataset.

Grid Search
===========

A grid search systematically runs different combinations of parameter
values on a dataset to see how each affects network reconstruction
results.

In SPRAS, users can define parameter grids for each algorithm directly
in the configuration file. When executed, SPRAS automatically runs each
algorithm across all parameter combinations and collects the resulting
subnetworks.

SPRAS will also include automatically narrowing down a parameter grid
for each algorithm on each dataset using a two-stage grid search.
Instead of tuning to a gold standard or a single metric, the search uses
graph topological heuristics (rules based on statistics like node count
and edge count) to discard subnetworks that are biologically
implausible. In the first stage, SPRAS runs each algorithm over a coarse
grid: a small set of parameter values spread across a wide range with
large gaps between them. Parameter combinations whose output subnetworks
pass the heuristics are kept, and the rest are discarded. Because the
underlying data differ from dataset to dataset, the set of passing
combinations also differs.

In the second stage, SPRAS refines the surviving combinations into a
finer grid. For each passing combination, it varies one parameter at a
time to sample values near the ones that worked. For example, if ``b =
5``, ``d = 10``, ``w = 2`` passed, SPRAS also tries neighbors such as
``w = 1`` and ``w = 3`` or ``d = 5`` and ``d = 15``. A neighbor is
evaluated as long as at least one of its adjacent coarse-grid values
passed, so the search can still explore just past the edge of the
passing region. The same heuristics filter these neighbors, and the
combinations that survive both stages form the final fine-tuned grid for
that algorithm and dataset.

Users can further refine these grids by rerunning the updated
configuration and adjusting the parameter ranges around the newly
identified regions to find and fine-tune the most promising algorithm
specific outputs for a given dataset.

.. note::

   Grid search features are still under development and will be added in
   future SPRAS releases.

**********************
 HTCondor integration
**********************

Running SPRAS locally can become slow and resource intensive, especially
when running many algorithms, parameter combinations, or datasets
simultaneously.

To address this, SPRAS supports an integration with `HTCondor
<https://htcondor.org/>`__ (a high throughput computing system),
allowing Snakemake jobs to be distributed in parallel and executed
across available compute.

See :doc:`Running with HTCondor <../htcondor>` for more information on
SPRAS's integrations with HTConder.

Ability to run with different container frameworks
==================================================

CHTC uses Apptainer to run containerized software in secure,
high-performance environments.

SPRAS accommodates this by allowing users to specify which container
framework to use globally within their workflow configuration.

The global workflow control section in the configuration file allows a
user to set which SPRAS supported container framework to use:

.. code:: yaml

   containers:
       framework: docker

The frameworks include Docker, Apptainer/Singularity, or dsub
