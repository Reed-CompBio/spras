Advanced Capabilities and Features
======================================

Evaluation
------------

Sometime user have a file where they can do evaluation on the outputs they are getting out
- not always the case though

we give option to provide gold standards and then have built in evaluation on those gold standards
- they are intertwined with the parameter selection in how those create the evaluation plots
- we have an option to do no parameter selection and see the outputs precision and recall directly

4. Gold Standards

Defines the input files SPRAS will use to evaluate output subnetworks

A gold standard dataset is comprised of: 

- a label: defines the name of the gold standard dataset
- node_file or edge_file: a list of either node files or edge files. Only one or the other can exist in a single dataset. At the moment only one edge or one node file can exist in one dataset
- data_dir: the path to where the input gold standard files live
- dataset_labels: a list of dataset labels that link each gold standard links to one or more datasets via the dataset labels

Parameter tuning
-----------------

More like these are all the things we can do with this, but will not be showing

- mention parameter tuning
- say that parameters are not preset and need to be tuned for each dataset

Picking params for algos hard; need a way to pick parameters

Grid Search
^^^^^^^^^^^^
write down the process a user can usually use

write down the method we use when trying to tune 1000s of dataset at the same time?

- or just the general one (coarse-> fine -optional> evaluation)

pick grids via graph hueristics

Parameter Selection
^^^^^^^^^^^^^^^^^^^^

show images of each of the selection methods if available

CHTC integration
-----------------

Running locally hard and slow when too many algo parameter datasets 
Need way to run long term
SPRAS runs jobs; CHTC can run these jobs in parallel when available

Ability to run with different container frameworks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

CHTC requires apptainer/singularity
- SPRAS allows a user to change the type of images to use 

1. Global Workflow Control

Sets options that apply to the entire workflow.

- Examples: the container framework (docker, singularity, dsub) and where to pull container images from

