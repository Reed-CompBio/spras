##########################################################
Intermediate Tutorial - Custom Data & Multi-Algorithm Runs
##########################################################

TODO: add an explanation of this tutorial

Step 1: Turn data into the input structure we require
=========================================

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
=========================================

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
- BowTieBuilder
- ResponseNet

Inputs
^^^^^^^
.. Each of these pathway reconstruction algorithms differ in the types of biological inputs they require and how they interpret those inputs to identify subnetworks.
.. Some algorithms require source and target nodes, reconstructing subnetworks that connect these predefined start and end points through the interactome.
.. Other algorithms use prizes, which are scores assigned to nodes of interest. These algorithms aim to identify subnetworks that contain or maximize the inclusion of prize nodes.
.. Finally, some algorithms use active nodes, representing nodes of interest that are significantly "on" or perturbed under a given biological condition. These algorithms focus on identifying and including these active regions within the reconstructed subnetwork.


These pathway reconstruction algorithms differ in the inputs nodes they require and how they interpret those nodes to identify subnetworks.
Some use source and target nodes to connect predefined start and end points, others use prizes, which are scores assigned to nodes of interest, and some rely on active nodes that represent proteins or genes significantly “on” or perturbed under specific biological conditions.

Along with differences in their inputs nodes, these algorithms also interpret the input interactome differently. 
Some can handle directed graphs, others work only with undirected graphs, and a few support mixed directionaltiy graphs.

SPRAS manages these differences automatically. 
It takes in a single SPRAS standardized dataset and then reformats and updates it internally to match the input requirements of each algorithm that is selected for the run. 
This ensures that every algorithm receives the correctly formatted data without requiring the user to prepare separate input files for each of the algorithms.

Parameters
^^^^^^^^^^
Each algorithm also exposes its own set of parameters that control its optimization strategy.
Some algorithms have no adjustable parameters, while others include multiple tunable settings that influence how subnetworks are created.
These parameters vary widely between algorithms and reflect the unique optimization techniques each method employs under the hood.

2.3 Running SPRAS with Multiple Algorithms
------------------------------------------

From the root directory spras/, run the command below from the command line:

.. code:: bash

    snakemake --cores 1 --configfile config/intermediate.yaml


What Happens When You Run This Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
What your directory structure should like after this run:

TODO: UPDATE THIS

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


1. Snakemake starts the workflow

Snakemake reads the options set in the intermediate.yaml configuration file and determines which datasets, algorithms, and parameter combinations need to run.  It also checks if any post-analysis steps were requested.

2. Preparing the dataset

SPRAS takes the interactome and node prize files specified in the config and bundles them into a Dataset object to be used for processing algorithm specific inputs. This object is stored as a .pickle file so it can be reused for other algorithms without re-processing it.

3. Creating algorithm specific inputs

For each algorithm marked as include: true in the config, SPRAS generates input files tailored to that algorithm. In this case, every algorithm is enabled, so SPRAS creates the files required for each algorithm.

4. Organizing results with parameter hashes

Each <dataset>-<algorithm>-params-<a hash> combination folder is created. A matching log file in logs/parameters-<algorithm>-params-<a hash>.yaml records the exact parameter values used.

5. Running the algorithm

SPRAS executes each algorithm by launching its corresponding Docker image multiple times (once for each parameter configuration). During each run, SPRAS provides the prepared input files and the corresponding parameter settings to the container. Each algorithm then runs independently within its Docker environment and produces a raw pathway output file (raw-pathway.txt), which contains the reconstructed subnetwork in the algorithm's native format.

6. Standardizing the results

SPRAS parses each of the raw output into a standardized SPRAS format (pathway.txt). This ensures all algorithms output are put into a standardized output, because their native formats differ.

7. Logging the Snakemake run 

Snakemake creates a dated log in .snakemake/log/. This log shows what rules ran and any errors that occurred during the SPRAS run.

2.4 Reviewing the pathway.txt Files 
-------------------------------------------
After running the intermediate configuration file, the output/intermediate/ directory will contain many more subfolders and files.
This is because we ran 11 algorithms, several of which were executed multiple times with different parameter combinations.

Just like in the beginner tutorial, each algorithm's results can be found in the spras/output/intermediate/ directory.
Within it, you'll see subfolders corresponding to each dataset-algorithm-parameter combination. 
Each folder contains a pathway.txt file that contains the reconstructed subnetwork for that specific run.

TODO CHOOSE NEW FILES
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

As you explore these files, you'll notice that the subnetworks vary widely across algorithms and parameter settings.
While you can still open and inspect these files manually, the number of outputs is much greater than in the beginner.yaml run, making manual inspection less practical.
The pathway.txt outputs serve as the foundation for further post-analysis, where you can systematically compare and interpret the reconstructed networks in greater detail.

In the next steps, we'll use SPRAS's internal post analyses tools to further explore and analyze these outputs.

Step 3: Use/Show summary stats and ML code
---------------------------------------------

To enable downstream analyses, update the analysis section in your configuration file by setting both summary, cytoscape, and ml, to true. Your analysis section in the configuration file should look like this:

.. code-block:: text

    analysis:
        summary:
            include: true
        cytoscape:
            include: true
        ml:
            include: true
            ... (ml parameters)

In this part of the tutorial, we're also including the ML section to enable machine learning-based post-analysis within SPRAS.

The machine learning (ML) analysis will performs unsupervised analyses such as Principal Component Analysis (PCA), Hierarchical Agglomerative Clustering (HAC), ensembling, and Jaccard similarity comparisons of the pathways.
- These analyses help uncover patterns and similarities between algorithms or across multiple outputs from the same algorithm
- The ML section includes configurable parameters that let you adjust the behavior of PCA, HAC, and the other ML analyses performed

After saving the changes in the configuration file, rerun with:

.. code:: bash

    snakemake --cores 1 --configfile config/intermediate.yaml



What the sturcutre should look at 

Look at the outputs and interpret what we see.