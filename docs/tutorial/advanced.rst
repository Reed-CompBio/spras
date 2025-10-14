Advanced Capabilities and Features
======================================

More like these are all the things we can do with this, but will not be showing

- mention parameter tuning
- say that parameters are not preset and need to be tuned for each dataset

CHTC integration

Anything not included in the config file

1. Global Workflow Control

Sets options that apply to the entire workflow.

- Examples: the container framework (docker, singularity, dsub) and where to pull container images from

running spras with multiple parameter combinations with multiple algorithms on multiple Datasets
- for the tutorial we are only doing one dataset

4. Gold Standards

Defines the input files SPRAS will use to evaluate output subnetworks

A gold standard dataset is comprised of: 

- a label: defines the name of the gold standard dataset
- node_file or edge_file: a list of either node files or edge files. Only one or the other can exist in a single dataset. At the moment only one edge or one node file can exist in one dataset
- data_dir: the path to where the input gold standard files live
- dataset_labels: a list of dataset labels that link each gold standard links to one or more datasets via the dataset labels
