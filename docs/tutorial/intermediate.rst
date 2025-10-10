##########################################################
Intermediate Tutorial - Custom Data & Multi-Algorithm Runs
##########################################################

This tutorial builds on the introduction to SPRAS from the previous tutorial. 
It guides participants through how to convert data into a format usable by pathway reconstruction algorithms, run multiple algorithms within a single workflow, and apply new tools to interpret and compare the resulting pathways.

You will learn how to:

- Prepare and format data for use with SPRAS
- Configure and run additional pathway reconstruction algorithms on a dataset
- Enable post-analysis steps to generate post analysis information

Step 1: Turn data into the input structure we require
======================================================

Show images and charts as to what is changing
0) download the data?

1) find the prizes using -log10
- people can just follow along with the ideas i'm doing?

2) find the sources and Source-Targets
- add the egfr pathway (cite it) and 
- add that we know that EGF is the start of the pathway and that we need a good connection between EGF and EGFR. 
- then we make everything else a target because they are important for the pathway

3) find the interactome
- find an updated one?

4) make the combined dataset

5) save the files to the input folder

6) add the code for people to download and run if they want?

7) need to add in the gold standard and the interactome
- I think I will just preprocess this?

8) save this data in inputs/

.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── ...
   ├── inputs/
   │   ├── THE DATA
   │   └── THE GOLD STANDARD
   │   └── THE NETWORK
   ├── outputs/
   │   └── basic/
   │       └── ... output files ...



Step 2: Adding multiple PRAs to the workflow
=============================================

Now that we've prepared our input data, we can begin running multiple pathway reconstruction algorithms on it.

For this part of the tutorial, we'll use a pre-defined configuration file that includes additional algorithms and post-analysis steps available in SPRAS.
Download it here: :download:`Intermediate Config File <../_static/config/intermediate.yaml>`

Save the file into the config/ folder of your SPRAS installation.

After adding this file, SPRAS will use the configuration to set up and reference your directory structure, which will look like this:

.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── basic.yaml
   │   └── intermediate.yaml
   ├── inputs/
   │   ├── THE DATA
   │   └── THE GOLD STANDARD
   │   └── THE NETWORK
   ├── outputs/
   │   └── basic/
   │       └── ... output files ...


2.1 Supported Algorithms in SPRAS
---------------------------------

SPRAS supports a wide range of algorithms, each designed around different biological assumptions and optimization strategies:

- Pathlinker
- Omics Integrator 1 
- Omics Integrator 2
- MEO
- Minimum-Cost Flow
- All pairs shortest paths
- Domino
- Source-Targets Random Walk with Restarts
- Random Walk with Restarts
- BowTieBuilder (Not optimized for large datasets; slower on big networks)
- ResponseNet

Wrapped Algorithms
^^^^^^^^^^^^^^^^^^^
Each algorithm has been wrapped by SPRAS. 
Wrapping an algorithm in SPRAS involves three main steps:

1. Input generation: SPRAS creates and formats the input files required by the algorithm based on the provided dataset
2. Execution: SPRAS runs the algorithm within its corresponding Docker container, which holds the algorithm code. This is called for each specified parameter combination in the configuration file.
3. Output Standardization: The raw outputs are converted into a standardized SPRAS format

Inputs
^^^^^^^
These pathway reconstruction algorithms differ in the inputs nodes they require and how they interpret those nodes to identify subnetworks.
Some use source and target nodes to connect predefined start and end points, others use prizes, which are scores assigned to nodes of interest, and some rely on active nodes that represent proteins or genes significantly “on” or perturbed under specific biological conditions.

Along with differences in their inputs nodes, these algorithms also interpret the input interactome differently. 
Some can handle directed graphs, others work only with undirected graphs, and a few support mixed directionaltiy graphs.

Parameters
^^^^^^^^^^
Each algorithm also exposes its own set of parameters that control its optimization strategy.
Some algorithms have no adjustable parameters, while others include multiple tunable settings that influence how subnetworks are created.
These parameters vary widely between algorithms and reflect the unique optimization techniques each method employs under the hood.

2.3 Running SPRAS with Multiple Algorithms
------------------------------------------
In the intermediate.yaml configuration file, it is set up have SPRAS run multiple algorithms (all of the algorithms supported in SPRAS except BowTieBuilder) with multiple parameter settings (if available) on one dataset.

From the root directory spras/, run the command below from the command line:

.. code:: bash

    snakemake --cores 4 --configfile config/intermediate.yaml


What Happens When You Run This Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

SPRAS will run more slowly than the beginner.yaml configuration. 
The same automated steps as in beginner.yaml (managed by Snakemake and Docker) run behind the scenes for intermediate.yaml; however, this configuration now runs multiple algorithms with different parameter combinations, which takes longer to complete.
By increasing the number of cores to 4, it allows Snakemake to parallelize the work locally, speeding up execution when possible.

1. Snakemake starts the workflow

Snakemake reads the options set in the intermediate.yaml configuration file and determines which datasets, algorithms, and parameter combinations need to run.  It also checks if any post-analysis steps were requested.

2. Preparing the dataset

SPRAS takes the interactome and node prize files specified in the configuration and bundles them into a Dataset object to be used for processing algorithm specific inputs. 
This object is stored as a .pickle file so it can be reused for other algorithms without re-processing it.

3. Creating algorithm specific inputs

For each algorithm marked as include: true in the configuration, SPRAS generates input files tailored to that algorithm. 
In this case, every algorithm is enabled, so SPRAS creates the files required for each algorithm.

4. Organizing results with parameter hashes

Each <dataset>-<algorithm>-params-<a hash> combination folder is created. 
A matching log file in logs/parameters-<algorithm>-params-<a hash>.yaml records the exact parameter values used.

5. Running the algorithm

SPRAS executes each algorithm by launching its corresponding Docker image multiple times (once for each parameter configuration). 
During each run, SPRAS provides the prepared input files and the corresponding parameter settings to the container. Each algorithm then runs independently within its Docker environment and produces a raw pathway output file (raw-pathway.txt), which contains the reconstructed subnetwork in the algorithm's native format.

6. Standardizing the results

SPRAS parses each of the raw output into a standardized SPRAS format (pathway.txt). 
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
   │   └── basic.yaml
   ├── inputs/
   │   ├── phosphosite-irefindex13.0-uniprot.txt
   │   └── tps-egfr-prizes.txt
   ├── outputs/
   │   └── basic/
   │       └── dataset-egfr-merged.pickle
   │       └── egfr-meo-params-FJBHHNE
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-meo-params-GKEDDFZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-meo-params-JQ4DL7K
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-meo-params-OXXIFMZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-mincostflow-params-42UBTQI
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-mincostflow-params-4G2PQRB
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator1-params-FZI2OGW
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator1-params-GUMLBDZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator1-params-PCWFPQW
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator2-params-EHHWPMD
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator2-params-IV3IPCJ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-4YXABT7
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-7S4SLU6
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-D4TUKMX
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-VQL7BDZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-rwr-params-34NN6EK
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-rwr-params-GGZCZBU
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-strwr-params-34NN6EK
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-strwr-params-GGZCZBU
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── logs
   │            └── datasets-egfr.yaml
   │            └── parameters-allpairs-params-BEH6YB2.yaml
   │            └── parameters-domino-params-V3X4RW7.yaml
   │            └── parameters-meo-params-FJBHHNE.yaml
   │            └── parameters-meo-params-GKEDDFZ.yaml
   │            └── parameters-meo-params-JQ4DL7K.yaml
   │            └── parameters-meo-params-OXXIFMZ.yaml
   │            └── parameters-mincostflow-params-42UBTQI.yaml
   │            └── parameters-mincostflow-params-4G2PQRB.yaml
   │            └── parameters-mincostflow-params-GGT4CVE.yaml
   │            └── parameters-omicsintegrator1-params-FZI2OGW.yaml
   │            └── parameters-omicsintegrator1-params-GUMLBDZ.yaml
   │            └── parameters-omicsintegrator1-params-PCWFPQW.yaml
   │            └── parameters-omicsintegrator2-params-EHHWPMD.yaml
   │            └── parameters-omicsintegrator2-params-IV3IPCJ.yaml
   │            └── parameters-pathlinker-params-4YXABT7.yaml
   │            └── parameters-pathlinker-params-7S4SLU6.yaml
   │            └── parameters-pathlinker-params-D4TUKMX.yaml
   │            └── parameters-pathlinker-params-VQL7BDZ.yaml
   │            └── parameters-rwr-params-34NN6EK.yaml
   │            └── parameters-rwr-params-GGZCZBU.yaml
   │            └── parameters-strwr-params-34NN6EK.yaml
   │            └── parameters-strwr-params-GGZCZBU.yaml
   │       └── prepared
   │            └── egfr-domino-inputs
   │                ├── active_genes.txt
   │                └── network.txt
   │            └── egfr-meo-inputs
   │                ├── edges.txt
   │                ├── sources.txt
   │                └── targets.txt
   │            └── egfr-mincostflow-inputs
   │                ├── edges.txt
   │                ├── sources.txt
   │                └── targets.txt
   │            └── egfr-omicsintegrator1-inputs
   │                ├── dummy_nodes.txt
   │                ├── edges.txt
   │                └── prizes.txt
   │            └── egfr-omicsintegrator2-inputs
   │                ├── edges.txt
   │                └── prizes.txt
   │            └── egfr-pathlinker-inputs
   │                ├── network.txt
   │                ── nodetypes.txt
   │            └── egfr-rwr-inputs
   │                ├── network.txt
   │                └── nodes.txt
   │            └── egfr-strwr-inputs
   |                ├── network.txt
   |                ├── sources.txt
   |                └── targets.txt

2.4 Reviewing the pathway.txt Files 
-------------------------------------------
After running the intermediate configuration file, the output/intermediate/ directory will contain many more subfolders and files.

Just like in the beginner tutorial, each algorithm's results can be found in the spras/output/intermediate/ directory.
Within it, you'll see subfolders corresponding to each dataset-algorithm-parameter combination. 
Each folder contains a pathway.txt file that contains the standardized reconstructed subnetwork for that specific run.

For example, the file egfr-mincostflow-params-42UBTQI/pathway.txt contains the following reconstructed subnetwork:

.. code-block:: text
        
    Node1	Node2	Rank	Direction
    CBL_HUMAN	EGFR_HUMAN	1	U
    EGFR_HUMAN	EGF_HUMAN	1	U
    EMD_HUMAN	LMNA_HUMAN	1	U
    FYN_HUMAN	KS6A3_HUMAN	1	U
    EGF_HUMAN	HDAC6_HUMAN	1	U
    HDAC6_HUMAN	HS90A_HUMAN	1	U
    KS6A3_HUMAN	SRC_HUMAN	1	U
    EGF_HUMAN	LMNA_HUMAN	1	U
    MYH9_HUMAN	S10A4_HUMAN	1	U
    EGF_HUMAN	S10A4_HUMAN	1	U
    EMD_HUMAN	SRC_HUMAN	1	U


And the file egfr-omicsintegrator1-params-GUMLBDZ/pathway.txt contains the following reconstructed subnetwork:

.. code-block:: text
        
    Node1	Node2	Rank	Direction
    CBLB_HUMAN	EGFR_HUMAN	1	U
    CBL_HUMAN	CD2AP_HUMAN	1	U
    CBL_HUMAN	CRKL_HUMAN	1	U
    CBL_HUMAN	EGFR_HUMAN	1	U
    CBL_HUMAN	PLCG1_HUMAN	1	U
    CDK1_HUMAN	NPM_HUMAN	1	D
    CHD4_HUMAN	HDAC2_HUMAN	1	U
    EGFR_HUMAN	EGF_HUMAN	1	U
    EGFR_HUMAN	GRB2_HUMAN	1	U
    EIF3B_HUMAN	EIF3G_HUMAN	1	U
    FAK1_HUMAN	PAXI_HUMAN	1	U
    GAB1_HUMAN	PTN11_HUMAN	1	U
    GRB2_HUMAN	PTN11_HUMAN	1	U
    GRB2_HUMAN	SHC1_HUMAN	1	U
    HDAC2_HUMAN	SIN3A_HUMAN	1	U
    HGS_HUMAN	STAM2_HUMAN	1	U
    KS6A1_HUMAN	MK01_HUMAN	1	U
    MK01_HUMAN	ABI1_HUMAN	1	D
    MK01_HUMAN	ERF_HUMAN	1	D
    MRE11_HUMAN	RAD50_HUMAN	1	U


As you explore more of these files, you'll notice that the subnetworks vary widely across algorithms and parameter settings.
While you can still open and inspect these files manually, the number of outputs is much greater than in the beginner.yaml run, making manual inspection less practical.
The pathway.txt outputs serve as the foundation for further post-analysis, where you can systematically compare and interpret the reconstructed networks in greater detail.

In the next steps, we'll use SPRAS's internal post analyses tools to further explore and analyze these outputs.

Step 3: Use ML Post-Analysis
=============================

To enable downstream analyses, update the analysis section in your configuration file by setting both summary, cytoscape, and ml, to true. Your analysis section in the configuration file should look like this:

.. code-block:: text

    analysis:
        ml:
            include: true

In this part of the tutorial, we're also including the machine learning (ml) section to enable machine learning-based post-analysis built within SPRAS.

The ml analysis will perform unsupervised analyses such as Principal Component Analysis (PCA), Hierarchical Agglomerative Clustering (HAC), ensembling, and Jaccard similarity comparisons of the pathways.
- These analyses help uncover patterns and similarities between different algorithms run on a given dataset
- if aggregate_per_algorithm: is set to true, it additionally groups outputs by algorithm within each dataset to uncover patterns and similarities for an algorithm
- The ML section includes configurable parameters that let you adjust the behavior of the ml analyses performed

With these updates, SPRAS will run the full set of unsupervised machine learning analyses across all outputs for a given dataset.

After saving the changes in the configuration file, rerun with:

.. code:: bash

    snakemake --cores 4 --configfile config/intermediate.yaml


What Happens When You Run This Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Reusing cached results

Snakemake reads the options set in intermediate.yaml and checks for any requested post-analysis steps. 
It reuses cached results; in this case, the pathway.txt files generated from the previously executed algorithms + parameter combinations on the egfr dataset.

2.	Running the ml analysis

SPRAS aggregates all files generated for a dataset.
These groupings include all the reconstructed subnetworks produced across algorithm for a given dataset (and, if enabled, grouped outputs per algorithm for a given dataset).
SPRAS then performs all machine learning analyses on each grouping and saves the results in the dataset-ml/ directory.


What Your Directory Structure Should Like After This Run:
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

   spras/
   ├── .snakemake/
   │   └── log/
   │       └── ... snakemake log files ...
   ├── config/
   │   └── basic.yaml
   ├── inputs/
   │   ├── phosphosite-irefindex13.0-uniprot.txt
   │   └── tps-egfr-prizes.txt
   ├── outputs/
   │   └── basic/
   │       └── dataset-egfr-merged.pickle
   │       └── egfr-meo-params-FJBHHNE
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-meo-params-GKEDDFZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-meo-params-JQ4DL7K
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-meo-params-OXXIFMZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-mincostflow-params-42UBTQI
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-mincostflow-params-4G2PQRB
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator1-params-FZI2OGW
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator1-params-GUMLBDZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator1-params-PCWFPQW
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator2-params-EHHWPMD
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-omicsintegrator2-params-IV3IPCJ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-4YXABT7
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-7S4SLU6
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-D4TUKMX
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-pathlinker-params-VQL7BDZ
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-rwr-params-34NN6EK
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-rwr-params-GGZCZBU
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-strwr-params-34NN6EK
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-strwr-params-GGZCZBU
   │            └── pathway.txt
   │            └── raw-pathway.txt
   │       └── egfr-ml
   │            └── ensemble-pathway.txt
   │            └── hac-clusters-horizontal.txt
   │            └── hac-clusters-vertical.txt
   │            └── hac-horizontal.png
   │            └── hac-vertical.png
   │            └── jaccard-heatmap.png
   │            └── jaccard-matrix.txt
   │            └── pca-coordinates.txt
   │            └── pca-variance.txt
   │            └── pca.png
   │       └── logs
   │            └── datasets-egfr.yaml
   │            └── parameters-allpairs-params-BEH6YB2.yaml
   │            └── parameters-domino-params-V3X4RW7.yaml
   │            └── parameters-meo-params-FJBHHNE.yaml
   │            └── parameters-meo-params-GKEDDFZ.yaml
   │            └── parameters-meo-params-JQ4DL7K.yaml
   │            └── parameters-meo-params-OXXIFMZ.yaml
   │            └── parameters-mincostflow-params-42UBTQI.yaml
   │            └── parameters-mincostflow-params-4G2PQRB.yaml
   │            └── parameters-mincostflow-params-GGT4CVE.yaml
   │            └── parameters-omicsintegrator1-params-FZI2OGW.yaml
   │            └── parameters-omicsintegrator1-params-GUMLBDZ.yaml
   │            └── parameters-omicsintegrator1-params-PCWFPQW.yaml
   │            └── parameters-omicsintegrator2-params-EHHWPMD.yaml
   │            └── parameters-omicsintegrator2-params-IV3IPCJ.yaml
   │            └── parameters-pathlinker-params-4YXABT7.yaml
   │            └── parameters-pathlinker-params-7S4SLU6.yaml
   │            └── parameters-pathlinker-params-D4TUKMX.yaml
   │            └── parameters-pathlinker-params-VQL7BDZ.yaml
   │            └── parameters-rwr-params-34NN6EK.yaml
   │            └── parameters-rwr-params-GGZCZBU.yaml
   │            └── parameters-strwr-params-34NN6EK.yaml
   │            └── parameters-strwr-params-GGZCZBU.yaml
   │       └── prepared
   │            └── egfr-domino-inputs
   │                ├── active_genes.txt
   │                └── network.txt
   │            └── egfr-meo-inputs
   │                ├── edges.txt
   │                ├── sources.txt
   │                └── targets.txt
   │            └── egfr-mincostflow-inputs
   │                ├── edges.txt
   │                ├── sources.txt
   │                └── targets.txt
   │            └── egfr-omicsintegrator1-inputs
   │                ├── dummy_nodes.txt
   │                ├── edges.txt
   │                └── prizes.txt
   │            └── egfr-omicsintegrator2-inputs
   │                ├── edges.txt
   │                └── prizes.txt
   │            └── egfr-pathlinker-inputs
   │                ├── network.txt
   │                ── nodetypes.txt
   │            └── egfr-rwr-inputs
   │                ├── network.txt
   │                └── nodes.txt
   │            └── egfr-strwr-inputs
   |                ├── network.txt
   |                ├── sources.txt
   |                └── targets.txt

Step 3.1: Reviewing the Outputs
--------------------------------

TODO: ADD SOME interpretATIONS

Ensembles
^^^^^^^^^

.. code-block:: text

    Node1	Node2	Frequency	Direction
    EGF_HUMAN	EGFR_HUMAN	0.42857142857142855	D
    EGF_HUMAN	S10A4_HUMAN	0.38095238095238093	D
    S10A4_HUMAN	MYH9_HUMAN	0.38095238095238093	D
    K7PPA8_HUMAN	MDM2_HUMAN	0.09523809523809523	D
    MDM2_HUMAN	P53_HUMAN	0.19047619047619047	D
    S10A4_HUMAN	K7PPA8_HUMAN	0.19047619047619047	D
    K7PPA8_HUMAN	SIR1_HUMAN	0.19047619047619047	D
    MDM2_HUMAN	MDM4_HUMAN	0.09523809523809523	D
    MDM4_HUMAN	P53_HUMAN	0.09523809523809523	D
    CD2A2_HUMAN	CDK4_HUMAN	0.09523809523809523	D
    CDK4_HUMAN	RB_HUMAN	0.09523809523809523	D
    MDM2_HUMAN	CD2A2_HUMAN	0.09523809523809523	D
    EP300_HUMAN	P53_HUMAN	0.2857142857142857	D
    K7PPA8_HUMAN	EP300_HUMAN	0.09523809523809523	D
    ...
    

HAC
^^^

.. image:: ../_static/images/hac-horizontal.png
   :alt: description of the image
   :width: 500
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>

.. image:: ../_static/images/hac-vertical.png
   :alt: description of the image
   :width: 300
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>

PCA
^^^

.. image:: ../_static/images/pca.png
   :alt: description of the image
   :width: 500
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>

Jaccard Similarity
^^^^^^^^^^^^^^^^^^

.. image:: ../_static/images/jaccard-heatmap.png
   :alt: description of the image
   :width: 500
   :align: center

.. raw:: html

   <div style="margin:20px 0;"></div>