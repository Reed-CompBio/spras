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

A grid search systematically checks different combinations of parameter
values to see how each affects network reconstruction results.

In SPRAS, users can define parameter grids for each algorithm directly
in the configuration file. When executed, SPRAS automatically runs each
algorithm across all parameter combinations and collects the resulting
subnetworks.

# TODO maybe add in information about how parameter tuning seems to be
done now # add in more details about two stage parameter tuning

SPRAS will also support parameter refinement using graph topological
heuristics. These topological metrics help identify parameter regions
that produce biologically plausible outputs networks. Based on these
heuristics, SPRAS will generate new configuration files with refined
parameter grids for each algorithm per dataset.

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

***********************
 Benchmarking Datasets
***********************

# add this part in # Should link to the benchmarking repo # We are
working on the vision of the live benchmarking website
