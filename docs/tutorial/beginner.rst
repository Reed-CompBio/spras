##################################################
Beginner Tutorial - Set up & Running One Algorithm
##################################################

This tutorial provides a hands-on introduction to SPRAS. It is designed to show participants how to install the software, run example workflows, and use tools to interpret the results.

You will learn how to:

- Set up the SPRAS software environment
- Explore the folder structure and understand how inputs, configurations, and outputs are organized
- Configure and run a pathway reconstruction algorithm on a provided dataset
- Enable post-analysis steps to generate post analysis information (summary statistics and Cytoscape visualizations)


Step 0: Clone the SPRAS repository, set up the environment, and run Docker
==========================================================================

0.1 Clone the SPRAS repository
-------------------------------

Visit the `SPRAS GitHub repository <https://github.com/Reed-CompBio/spras>`__ and clone it locally

0.2 Set up the SPRAS environment
-------------------------------------

From the root directory of the SPRAS repository, create and activate the Conda environment and install the SPRAS python package:

.. code:: bash

    conda env create -f environment.yml
    conda activate spras
    python -m pip install .

.. note::
   The first command performs a one time setup of the SPRAS dependencies by creating a Conda environment (an isolated space that keeps all required packages and versions separate from your system).

   The second command activates the newly created environment so you can use these dependencies when running SPRAS; this step must be done each time you open a new terminal session.

   The last command is a one time installation of the SPRAS package into the environment.

0.3 Test the installation
-------------------------

Run the following command to confirm that SPRAS has been set up successfully from the command line:

.. code:: bash

   python -c "import spras; print('SPRAS import successful')"

0.4 Start Docker
----------------

Before running SPRAS, make sure Docker Desktop is running.

Launch Docker Desktop and wait until it says "Docker is running".
   
.. note::
   SPRAS itself does not run inside a Docker container.
   However, Docker is required because SPRAS uses it to execute individual pathway reconstruction algorithms and certain post-analysis steps within isolated containers.
   These containers include all the necessary dependencies to run each algorithm or post analysis.

Step 1: Explanation of configuration file
=========================================

A configuration file specifies how a SPRAS workflow should run; think of it as the control center for the workflow.

It defines which algorithms to run, the parameters to use, the datasets and gold standards to include, the analyses to perform after reconstruction, and the container settings for execution. 

The configuration files used are written in YAML, a human-readable format that uses simple indentation and key-value pairs for data seralizaiton.

SPRAS uses Snakemake to read the YAML configuration file and execute a SPRAS workflow accordingly.

.. Snakemake considers a task from the configuration file complete once the expected output files are present in the output directory. 
.. As a result, rerunning the same configuration file may do nothing if those files already exist. 
.. To continue or rerun SPRAS with the same configuration file, delete the output directory (or its contents) or modify the configuration file so Snakemake regenerates new results.

For this part of the tutorial, we'll use a pre-defined configuration file. 
Download it here: :download:`Beginner Config File <../_static/config/beginner.yaml>`

Save the file into the config/ folder of your SPRAS installation.
After adding this file, your directory structure will look like this (ignoring the rest of the folders):

.. code-block:: text

   spras/
   ├── config/
   │   └── beginner.yaml
   ├── inputs/
   │   ├── phosphosite-irefindex13.0-uniprot.txt # pre-defined in SPRAS already, used by the beginner.yaml file
   │   └── tps-egfr-prizes.txt # pre-defined in SPRAS already, used by the beginner.yaml file

config/
-------

The config/ folder stores configuration files for SPRAS.

.. note::
   You can name or place configuration files anywhere, as long as you provide the correct path when running SPRAS (explained later in this tutorial).

input/
------

The inputs/ folder contains input data files.
You can use the provided example datasets or add your own for custom experiments to this folder.

.. note::
   Input files can be stored anywhere as long as their paths are correctly referenced in the configuration file (explained later in this tutorial).

Here's an overview of the major sections when looking at a configuration file:

Algorithms
-----------

.. code-block:: yaml
    
    algorithms:
    - name: omicsintegrator1
      params:
         include: true
         run1:
            b: 0.1
            d: 10
            g: 1e-3
         run2:
            b: [0.55, 2, 10]
            d: [10, 20]
            g: 1e-3
   

When defining an algorithm in the configuration file, its name must match one of the supported SPRAS algorithms (introduced in the intermediate tutorial / more information on the algorithms can be found under the Supported Algorithms section). 
Each algorithm includes an include flag, which you set to true to have Snakemake run it, or false to disable it. 

Algorithm parameters can be organized into one or more run blocks (e.g., run1, run2, …), with each block containing key-value pairs.
When defining a parameter, it can be passed as a single value or passed by listing parameters within a list.
If multiple parameters are defined as lists within a run block, SPRAS generates all possible combinations (Cartesian product) of those list values together with any fixed single-value parameters in the same run block. 
Each unique combination runs once per algorithm.

Datasets
--------

.. code-block:: yaml

    datasets:
    - 
        label: egfr
        node_files: ["prizes.txt", "sources-targets.txt"]
        edge_files: ["interactome.txt"]
        other_files: []
        data_dir: "input"
    
In the configuration file, datasets are defined under the datasets section. 
Each dataset you define will be run against all of the algorithms enabled in the configuration file.

The dataset must include the following types of keys and files:

- label: a name that uniquely identifies a dataset throughout the SPRAS workflow and outputs.
- node_files: Input files listing the “prizes” or important starting nodes ("sources" or "targets") for the algorithm
- edge_files: Input interactome or network file that defines the relationships between nodes
- other_files: This placefolder is not used
- data_dir: The file path of the directory where the input dataset files are located

Reconstruction Settings
-----------------------

.. code-block:: yaml

    reconstruction_settings:
    locations:
        reconstruction_dir: "output"


The reconstruction_settings section controls where outputs are stored.
Set reconstruction_dir to the directory path where you want results saved. SPRAS will automatically create this folder if it doesn't exist.
If you are running multiple configuration files, you can set unique paths to keep outputs organized and separate.

Analysis
--------

.. code-block:: yaml

    analysis:
    summary:
        include: true
    cytoscape:
        include: true
    ml:
        include: true
   


SPRAS includes multiple downstream analyses that can be toggled on or off directly in the configuration file. 
When enabled, these analyses are performed per dataset and produce summaries or visualizations of the results from all enabled algorithms for that dataset.

.. note::
   The configuration file and sections shown here do not represent the full set of options available in SPRAS.
   
   The SPRAS documentation is still under construction, and the examples provided (like beginner.yaml) only show the basic configuration needed for this tutorial.
   
   To see a more complete set of configurable options and parameters, refer to the full examples in config/config.yaml and config/egfr.yaml within the SPRAS repository.

Step 2: Running SPRAS on a provided example dataset 
====================================================

2.1 Running SPRAS with the Beginner Configuration
-------------------------------------------------
In the beginner.yaml configuration file, it is set up have SPRAS run a single algorithm with one parameter setting on one dataset.

From the root directory spras/, run the command below from the command line:

.. code:: bash

    snakemake --cores 1 --configfile config/beginner.yaml

What Happens When You Run This Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
SPRAS will executes quickly from your perspective; however, several automated steps (handled by Snakemake and Docker) occur behind the scenes. 
(ADD IN THAT APPLE COMPUTETERS WILL TAKE A SECOND BECAUSE OUR DOCKER IMAGES ARE AMD AND NOT ARM)


1. Snakemake starts the workflow

Snakemake reads the options set in the beginner.yaml configuration file and determines which datasets, algorithms, and parameter combinations need to run and if any post-analysis steps were requested.

2. Preparing the dataset

SPRAS takes the interactome and node prize files specified in the configuration and bundles them into a Dataset object to be used for processing algorithm specific inputs. 
This object is stored as a .pickle file (e.g. dataset-egfr-merged.pickle) so it can be reused for other algorithms without re-processing it.

3. Creating algorithm specific inputs

For each algorithm marked as include: true in the configuration, SPRAS generates input files tailored to that algorithm using the input standardized egfr dataset. 
In this case, only PathLinker is enabled. 
SPRAS creates the network.txt and nodetypes.txt files required by PathLinker in the prepared/egfr-pathlinker-inputs/.

4. Organizing results with parameter hashes

Each dataset-algorithm-parameter combination is placed in its own folder named like egfr-pathlinker-params-D4TUKMX/. 
D4TUKMX is a hash that uniquely identifies the specific parameter combination (k = 10 here). 
A matching log file in logs/parameters-pathlinker-params-D4TUKMX.yaml records the exact parameter values.

5. Running the algorithm

SPRAS launches the PathLinker Docker image that it downloads from DockerHub, sending it the prepared files and parameter settings.
PathLinker runs and produces a raw pathway output file (raw-pathway.txt) that holds the subnetwork it found in its own native format.

6. Standardizing the results

SPRAS parses the raw PathLinker output into a standardized SPRAS format (pathway.txt). 
This ensures all algorithms output are put into a standardized output, because their native formats differ.

7. Logging the Snakemake run 

Snakemake creates a dated log in .snakemake/log/. This log shows what rules ran and any errors that occurred during the SPRAS run.

What Your Directory Structure Should Like After This Run:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── beginner.yaml
   ├── inputs/
   │   ├── phosphosite-irefindex13.0-uniprot.txt
   │   └── tps-egfr-prizes.txt
   ├── outputs/
   │   └── beginner/
   │       └── egfr-pathlinker-params-D4TUKMX/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── logs/
   │                └── dataset-egfr.yaml
   │                └── parameters-pathlinker-params-D4TUKMX.yaml
   │       └── prepared/
   │            └── egfr-pathlinker-inputs
   │                └── network.txt
   │                └── nodetypes.txt
   │       └── dataset-egfr-merged.pickle


Step 2.2: Overview of the SPRAS Folder Structure
=================================================

After running the SPRAS command, you'll see that the folder structure includes four main directories that organize everything needed to run workflows and store their results.

.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── ... other configs ...
   ├── inputs/
   │   └── ... input files ...
   ├── outputs/
   │   └── ... output files ...

.snakemake/log/
---------------

The .snakemake/log/ directory contains records of all Snakemake jobs that were executed for the SPRAS run, including any errors encountered during those runs.

config/
-------

Holds configuration files (YAML) that define which algorithms to run, what datasets to use, and which analyses to perform.

input/
------

Contains the input data files, such as interactome edge files and input nodes. This is where you can place your own datasets when running custom experiments.

output/
-------

Stores all results generated by SPRAS. Subfolders are created automatically for each run, and their structure can be controlled through the configuration file.

By default, the directories are named to be config/, input/, and output/. The config/, input/, and output/ folders can be placed anywhere and named anything within the SPRAS repository. Their input/ and output/ locations can be updated in the configuration file, and the configuration file itself can be set by providing its path when running the SPRAS command.
SPRAS has additional files and directories to use during runs. However, for most users, and for the purposes of this tutorial, it isn't necessary to fully understand them.


2.4 Running SPRAS with More Parameter Combinations
---------------------------------------------------

In the beginner.yaml configuration file, uncomment the run2 section under pathlinker so it looks like:

.. code-block:: yaml
    
    run2:   
        k: [10, 100] 

With this update, the beginner.yaml configuration file is set up have SPRAS run a single algorithm with multiple parameter settings on one dataset.

After saving the changes, rerun with:

.. code:: bash

    snakemake --cores 1 --configfile config/beginner.yaml

What Happens When You Run This Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.	Snakemake loads the configuration file

Snakemake reads beginner.yaml to determine which datasets, algorithms, parameters, and post-analyses to run. 
It reuses cached results to skip completed steps, rerunning only those that are new or outdated. 
Here, the dataset pickle, PathLinker inputs, and D4TUKMX parameter set are reused instead of rerun.

2. Organizing outputs per parameter combination

Each new dataset-algorithm-parameter combination gets its own folder (e.g egfr-pathlinker-params-7S4SLU6/ and egfr-pathlinker-params-VQL7BDZ/)
The hashes 7S4SLU6 and VQL7BDZ uniquely identifies the specific set of parameters used.

3. Reusing prepared inputs with additional parameter combinations

Since PathLinker has already been run once, SPRAS uses the cached prepared inputs (network.txt, nodetypes.txt) rather than regenerating them.
For each new parameter combination, SPRAS executes the PathLinker by launching its corresponding Docker image multiple times (once for each parameter configuration). 
PathLinker then runs and produces a raw-pathway.txt file specific to each parameter hash.

4. Parsing into standardized results

SPRAS parses each new raw-pathway.txt file into a standardized SPRAS format (pathway.txt).

What Your Directory Structure Should Like After This Run:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── beginner.yaml
   ├── inputs/
   │   ├── phosphosite-irefindex13.0-uniprot.txt
   │   └── tps-egfr-prizes.txt
   ├── outputs/
   │   └── beginner/
   │       └── egfr-pathlinker-params-7S4SLU6/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-D4TUKMX/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-VQL7BDZ/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── logs/
   │                └── dataset-egfr.yaml
   │                └── parameters-pathlinker-params-7S4SLU6.yaml
   │                └── parameters-pathlinker-params-D4TUKMX.yaml
   │                └── parameters-pathlinker-params-VQL7BDZ.yaml
   │       └── prepared/
   │            └── egfr-pathlinker-inputs
   │                └── network.txt
   │                └── nodetypes.txt
   │       └── dataset-egfr-merged.pickle


2.5 Reviewing the pathway.txt Files 
-------------------------------------------

Each algorithm and parameter combination produces a corresponding pathway.txt file. 
These files contain the reconstructed subnetworks and can be used at face value, or for further post analysis.

1.	Locate the files

Navigate to the output directory spras/output/beginner/. Inside, you will find subfolders corresponding to each dataset-algorithm-parameter combination.

2. Open a pathway.txt file

Each file lists the network edges that were reconstructed for that specific run. The format includes columns for the two interacting nodes, the rank, and the edge direction

For example, the file egfr-pathlinker-params-7S4SLU6/pathway.txt contains the following reconstructed subnetwork:

.. code-block:: text
        
    Node1	Node2	Rank	Direction
    EGF_HUMAN	EGFR_HUMAN	1	D
    EGF_HUMAN	S10A4_HUMAN	2	D
    S10A4_HUMAN	MYH9_HUMAN	2	D
    K7PPA8_HUMAN	MDM2_HUMAN	3	D
    MDM2_HUMAN	P53_HUMAN	3	D
    S10A4_HUMAN	K7PPA8_HUMAN	3	D
    K7PPA8_HUMAN	SIR1_HUMAN	4	D
    MDM2_HUMAN	MDM4_HUMAN	5	D
    MDM4_HUMAN	P53_HUMAN	5	D
    CD2A2_HUMAN	CDK4_HUMAN	6	D
    CDK4_HUMAN	RB_HUMAN	6	D
    MDM2_HUMAN	CD2A2_HUMAN	6	D
    EP300_HUMAN	P53_HUMAN	7	D
    K7PPA8_HUMAN	EP300_HUMAN	7	D
    K7PPA8_HUMAN	UBP7_HUMAN	8	D
    UBP7_HUMAN	P53_HUMAN	8	D
    K7PPA8_HUMAN	MDM4_HUMAN	9	D
    MDM4_HUMAN	MDM2_HUMAN	9	D

The pathway.txt files serve as the foundation for further analysis, allowing you to explore and interpret the reconstructed networks in greater detail.
In this case you can visulize them in cytoscape or compare their statistics to better understand these outputs.


Step 3: Running Post-Analyses within SPRAS
==========================================
To enable downstream analyses, update the analysis section in your configuration file by setting both summary and cytoscape to true. Your analysis section in the configuration file should look like this:

.. code-block:: yaml

    analysis:
        summary:
            include: true 
        cytoscape:
            include: true 

summary generates graph topological summary statistics  for each algorithm's parameter combination output, generating a summary file for all reconstructed subnetworks for each dataset.
This post analysis will report these statistics for each pathway:

- Number of nodes
- Number of edges
- Number of connected components
- Network density
- Maximum degree
- Median degree
- Maximum diameter
- Average path length

cytoscape creates a Cytoscape session file (.cys) containing all reconstructed subnetworks for each dataset, making it easy to upload and visualize them directly in Cytoscape.

With this update, the beginner.yaml configuration file is set up for SPRAS to run two post-analyses on the outputs generated by a single algorithm that was executed with multiple parameter settings on one dataset.

After saving the changes, rerun with:

.. code:: bash

    snakemake --cores 1 --configfile config/beginner.yaml


What Happens When You Run This Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Reusing cached results

Snakemake reads the options set in beginner.yaml and checks for any requested post-analysis steps. 
It reuses cached results; in this case, the pathway.txt files generated from the previously executed PathLinker parameter combinations for the egfr dataset.

2.	Running the summary analysis

SPRAS aggregates the pathway.txt files from all selected parameter combinations into a single summary table. 
The results are saved in egfr-pathway-summary.txt.

3.	Running the Cytoscape analysis

All pathway.txt files from the chosen parameter combinations are collected and passed into the Cytoscape Docker image. 
A Cytoscape session file is then generated, containing visualizations for each pathway and saved as egfr-cytoscape.cys.

What Your Directory Structure Should Like After This Run:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── beginner.yaml
   ├── inputs/
   │   ├── phosphosite-irefindex13.0-uniprot.txt
   │   └── tps-egfr-prizes.txt
   ├── outputs/
   │   └── beginner/
   │       └── egfr-pathlinker-params-7S4SLU6/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-D4TUKMX/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-VQL7BDZ/
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── logs/
   │                └── dataset-egfr.yaml
   │                └── parameters-pathlinker-params-7S4SLU6.yaml
   │                └── parameters-pathlinker-params-D4TUKMX.yaml
   │                └── parameters-pathlinker-params-VQL7BDZ.yaml
   │       └── prepared/
   │            └── egfr-pathlinker-inputs
   │                └── network.txt
   │                └── nodetypes.txt
   │       └── dataset-egfr-merged.pickle
   │       └── egfr-cytoscape.cys
   │       └── egfr-pathway-summary.txt

Step 3.1: Reviewing the Outputs
-----------------------------------

Reviewing Summary Files
^^^^^^^^^^^^^^^^^^^^^^^^
1. Open the summary statistics file

In your file explorer, go to spras/output/beginner/egfr-pathway-summary.txt and open it locally.

.. image:: ../_static/images/summary-stats.png
   :alt: description of the image
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>


This file summarizes the graph topological statistics for each output pathway.txt file for a given dataset, 
along with the parameter combinations that produced them, allowing you to interpret and compare algorithm outputs side by side in a compact format.

Reviewing Outputs in Cytoscape
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.	Open Cytoscape

Launch the Cytoscape application on your computer.

2.	Load the Cytoscape session file

Navigate to spras/output/beginner/egfr-cytoscape.cys and open it in Cytoscape.

.. image:: ../_static/images/cytoscape_upload_network.png
   :alt: description of the image
   :width: 500
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>
   
.. image:: ../_static/images/cytoscape-open-cys-file.png
   :alt: description of the image
   :width: 500
   :align: center


.. raw:: html

   <div style="margin:20px 0;"></div>

Once loaded, the session will display all reconstructed subnetworks for a given dataset, organized by algorithm and parameter combination.

.. image:: ../_static/images/cytoscape-opened.png
   :alt: description of the image
   :width: 500
   :align: center

You can view and interact with each reconstructed subnetwork. Compare how the different parameter settings influence the pathways generated.

The small parameter value (k=1) produced a compact subnetwork:

.. image:: ../_static/images/1_pathway.png
   :alt: description of the image
   :width: 400
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>


The moderate parameter value (k=10) expanded the subnetwork, introducing additional nodes and edges that may uncover new connections:

.. image:: ../_static/images/10_pathway.png
   :alt: description of the image
   :width: 600
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>

The large parameter value (k=100) generates a much denser subnetwork, capturing a broader range of edges but also could introduce connections that may be less  meaningful:

.. image:: ../_static/images/100_pathway.png
   :alt: description of the image
   :width: 600
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>