# Running PathLinker
Before running pathway reconstruction algorithms through SPRAS, it can be informative to see how they are typically run without SPRAS.
This document describes PathLinker and how to run the PathLinker software.

## Step 1: Read about PathLinker

PathLinker takes as input (1) a weighted, directed protein-protein interaction (PPI) network, (2) two sets of nodes: a source set (representing receptors of a pathway of interest) and a target set (representing transcriptional regulators of a pathway of interest), and (3) an integer _k_. PathLinker efficiently computes the _k_-shortest paths from any source to any target and returns the subnetwork of the top _k_ paths as the pathway reconstruction.  Later work expanded PathLinker by incorporating protein localization information to re-score tied paths, dubbed Localized PathLinker (LocPL).

**References:**
- Ritz et al. Pathways on demand: automated reconstruction of human signaling networks.  _NPJ Systems Biology and Applications._ 2016. [doi:10.1038/npjsba.2016.2](https://doi.org/10.1038/npjsba.2016.2)
- Youssef, Law, and Ritz. Integrating protein localization with automated signaling pathway reconstruction. _BMC Bioinformatics._ 2019. [doi:10.1186/s12859-019-3077-x](https://doi.org/10.1186/s12859-019-3077-x)

We will focus on the original 2016 version of PathLinker.
Start by reading this manuscript to gain a high-level understanding of its algorithm, functionality, and motivation.

## Step 2: Get the PathLinker files

From the PathLinker GitHub repository <https://github.com/Murali-group/PathLinker>, click Code and Download ZIP to download all the source and data files.
Unzip them on your local file system into a directory you’ll use for this project.

## Step 3: Install Anaconda (optional)

If you do not already have Anaconda on your computer, install Anaconda so you can manage conda environments.
If you haven’t used conda before for Python, this [blog post](https://astrobiomike.github.io/unix/conda-intro) gives an overview of conda and why it is useful.
You don’t need most of the commands in it, but it can be a reference.
You can download Anaconda from <https://www.anaconda.com/download> and follow the installation instructions.
If you have the option to add Anaconda to your system `PATH` when installing it, which will make it your default version of Python, we recommend that.
Anaconda will give you an initial default conda environment and some useful packages.
A conda environment is an isolated collection of Python packages that enables you to have multiple versions of Python and packages installed in parallel for different projects, which often require different versions of their dependencies.

## Step 4: Create a conda environment for PathLinker

Create a new conda environment for PathLinker called "pathlinker" with Python 3.5 and install the dependencies from a requirements file into that environment.
PathLinker uses old versions of Python and dependencies like networkx, a package for working with graphs in Python.
The `requirements.txt` file contains an uninstallable package, so open it in a text editor and delete the line
```
pkg-resources==0.0.0
```

Then, from the project directory you created that contains the `requirements.txt` file from the PathLinker repository run:
```
conda create -n pathlinker python=3.5
conda activate pathlinker
pip install -r requirements.txt
```
The first command creates a new environment called "pathlinker" with the old version of Python.
You only do this once.
The second command activates that environment so you can use those packages.
You need to do this second command every time before running PathLinker.
The third command installs the required dependencies and is only needed once.

## Step 5: Run PathLinker on example data

Change (`cd`) into the example directory and try running the example command
```
python ../run.py sample-in-net.txt sample-in-nodetypes.txt
```
If it works, open the two input files and the output file(s).
See if what PathLinker has done makes sense.
The input network file lists one edge in the graph per line.
The node types file tells you which nodes are the special sources and targets.

## Step 6: Change the PathLinker options and see how the behavior changes

PathLinker's command line interface does not have extensive documentation in its GitHub repository.
We can see the supported command line arguments in the source code at <https://github.com/Murali-group/PathLinker/blob/master/run.py#L32>
These lines list the argument, the default value, and a short description.
For example, the `-k` argument sets the value of _k_ discussed in the manuscript, the number of shortest paths.
Try setting this to a very small value like 1 or 2 or 3.
That will make it easier to inspect the output files.
Try adjusting other PathLinker arguments and observe the effects on the output.

## Note for Windows users

When running PathLinker or other software on Windows, the default Command Prompt is not recommended for command line programs.
[Git Bash](https://gitforwindows.org/) is one recommended alternative terminal that is a standalone program.
The [Windows Subsystem for Linux](https://learn.microsoft.com/en-us/windows/wsl/install) also runs a full Linux distribution through Windows, which includes a terminal.
