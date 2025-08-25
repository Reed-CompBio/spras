Basic Tutorial - Set up & Running One Algorithm
=================================================

TODO: add an explanation of this tutorial

Step 0: Clone the SPRAS repository, set up the environment, and run Docker
--------------------------------------------------------------------------

1. Start Docker

Launch Docker Desktop and wait until it says "Docker is running".

2. Clone the SPRAS repository

Visit the `SPRAS github repository <https://github.com/Reed-CompBio/spras>`__ and clone it locally

3. 	Set up the SPRAS environment

From the root directory of the SPRAS repository, create and activate the Conda environment:

.. code:: bash

    conda env create -f environment.yml
    conda activate spras
    python -m pip install .

4. Test the installation

Run the example Snakemake workflow to confirm everything is working:

.. code:: bash

    snakemake --cores 1 --configfile config/config.yaml

This will run SPRAS using the example config file (config/config.yaml) and input files. 
SPRAS will automatically pull any missing Docker images as long as Docker is running.
Results will be written to the output directory.

Step 1: Explanation of Configuration File
------------------------------------------

A configuration file controls how SPRAS runs.  It defines which algorithms to run, the parameters to use, the datasets and gold standards to include, the analyses to perform after reconstruction, and the container settings for execution. Think of it as the control center for the workflow.

SPRAS uses the Snakemake workflow manager, which reads the configuration file to build and execute the workflow. Snakemake marks a task as complete once the expected output files are present in the output directory. As a result, rerunning the same configuration may do nothing if those files already exist. To continue running SPRAS, you can either remove the output directory (or its contents) or update the configuration file so that Snakemake generates new results.

Here’s an overview of the major sections looking at config/config.yaml as an example:

1. Global Workflow Control

Sets options that apply to the entire workflow.

- Examples: the container framework (docker, singularity, dsub), where to pull container images from, and technical settings like hash_length.

2. Algorithms

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

- Each algorithm has an include flag (true/false) to turn it on or off.
- Parameters are specified under params. If multiple parameter values are listed, SPRAS will run the algorithm once for every combination (a parameter sweep).
- This section is where you decide which methods you want to try and how they’re tuned.

3. Datasets

Defines the input files SPRAS will use to run pathway reconstruction

A dataset is comprised of: 

- a label: defines the name of the dataset
- node_files: the input nodes to use that are the molecules of interest (sources, targets, prizes, actives, dummy nodes)
- edge_files: the interactome
- data_dir: the path to where the input dataset files live
- other_files: a placefolder for potential need for future delevvelopment

4. Gold Standards

Defines the input files SPRAS will use to evaluate output subnetworks

A gold standard dataset is comprised of: 

- a label: defines the name of the gold standard dataset
- node_file or edge_file: a list of either node files or edge files. Only one or the other can exist in a single dataset. At the moment only one edge or one node file can exist in one dataset
- data_dir: the path to where the input gold standard files live
- dataset_labels: a list of dataset labels that link each gold standard links to one or more datasets via the dataset labels

5. Reconstruction Settings

- Defines the filepath where reconstructed networks are saved (output directory by default)
- Basic housekeeping for how SPRAS organizes and stores results.

6. Analysis

Controls which types of post-analysis are run:

- Summary statistics: calculates metrics per dataset for each algorithm
- Cytoscape export: generates .cys session files for each output subnetwork for easy visualization
- Machine learning (ML): PCA, HAC, ensembling, and jaccard similarity that is run between algortihmns and per algorithm
- Evaluation: Compares reconstructed pathways against the gold standards using different parameter selections
- Each analysis has an include: true/false toggle

Step 2: Explanation of SPRAS Folders
-------------------------------------

After cloning SPRAS, you will see three main folders that organize everything needed to run and analyze workflows:

1. config/

Holds configuration files (YAML) that define which algorithms to run, what datasets to use, and which analyses to perform.

2. input/

Contains the input data files, such as interactome edge files and input nodes. This is where youcan place your own datasets when running custom experiments.

TODO: show the input types?

3. output/

Stores all results generated by SPRAS. Subfolders are created automatically for each run, and their structure can be controlled through the configuration file.

TODO: add that the config, input, and output folders can be set to new locations in the configuration file. As default, they are config/, input/ and ouput/

Step : Running SPRAS on a provided example dataset 
---------------------------------------------------

- egfr 
- one algorithm
- three different preset combos
- have them make the configuration file?
- provide a template to use?


Step : Understanding the Outputs / Visulizing the Outputs
-----------------------------------------------------------

