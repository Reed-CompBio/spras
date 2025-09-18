Intermediate Tutorial - Custom Data & Multi-Algorithm Runs
============================================================

TODO: add an explanation of this tutorial

Step 1: Turn data into the input structure we require
-----------------------------------------------------

TODO: show the different input types?
allow people to do one or the other

Step 2: Adding multiple PRAs to the workflow
---------------------------------------------

1. Algorithms

- Lists all supported pathway reconstruction algorithms

    - Pathlinker
    - Omics Integrator 1
    - Omics Integrator 2
    - MEO
    - Minimum-Cost Flow
    - All pairs shortest paths
    - Domino
    - Source-Targets Random Walk with Restarts
    - Random Walk with Restarts
    - Bow Tie Builder
    - ResponseNet 


Step 3: Use/Show summary stats and ML code
---------------------------------------------

4. Gold Standards

Defines the input files SPRAS will use to evaluate output subnetworks

A gold standard dataset is comprised of: 

- a label: defines the name of the gold standard dataset
- node_file or edge_file: a list of either node files or edge files. Only one or the other can exist in a single dataset. At the moment only one edge or one node file can exist in one dataset
- data_dir: the path to where the input gold standard files live
- dataset_labels: a list of dataset labels that link each gold standard links to one or more datasets via the dataset labels

6. Analysis

Controls which types of post-analysis are run, for this part of the tutorial:

- Machine learning (ML): PCA, HAC, ensembling, and jaccard similarity that is run between algortihmns and per algorithm
- Evaluation: Compares reconstructed pathways against the gold standards using different parameter selections
- Each analysis has an include: true/false toggle