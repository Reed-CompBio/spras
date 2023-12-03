# SPRAS contribution guide
The SPRAS maintainers welcome external contributions.
Code contributions will be licensed using the project's [MIT license](LICENSE).

## Contributing a new pathway reconstruction guide
This guide walks new contributors through the process of adding a new pathway reconstruction algorithm to SPRAS.
It follows the checklist below step-by-step to add a simple algorithm called Local Neighborhood.

### Prerequisites
SPRAS builds on multiple technologies to run pathway reconstruction in a Snakemake workflow.
Before following this guide, a contributor will need
- Familiarity with Python ([Carpentries introduction](https://swcarpentry.github.io/python-novice-inflammation/))
- Familiarity with Git and GitHub ([Carpentries introduction](https://swcarpentry.github.io/git-novice/))
- Familiarity with Docker and Dockerfiles to create images ([Carpentries introduction](https://carpentries-incubator.github.io/docker-introduction/))
- A [Docker Hub](https://hub.docker.com/) account

It is not necessary to have experience with Snakemake, Python testing, or pandas before getting started, but it may help with more complex SPRAS contributions:
- Snakemake [Carpentries introduction](https://carpentries-incubator.github.io/workflows-snakemake/) or [beginner's guide](http://ivory.idyll.org/blog/2023-snakemake-slithering-section-1.html)
- pytest [getting started](https://docs.pytest.org/en/7.1.x/getting-started.html) and [how-to guides](https://docs.pytest.org/en/7.1.x/how-to/index.html)
- pandas [Carpentries introduction](https://datacarpentry.org/python-ecology-lesson/02-starting-with-data.html) or [10 minutes to pandas](https://pandas.pydata.org/pandas-docs/stable/user_guide/10min.html)

### Step 0: Fork the repository and create a branch
From the [SPRAS repository](https://github.com/Reed-CompBio/spras), click the "Fork" button in the upper right corner to create a copy of the repository in your own GitHub account.
Do not change the "Repository name".
Then click the green "Create fork" button.

The simplest way to set up SPRAS for local development is to clone your fork of the repository to your local machine.
You can do that with a graphical development environment or from the command line.
After cloning the repository, create a new git branch called `local-neighborhood` for local neighborhood development.
In the following commands, replace the example username `agitter` with your GitHub username.
```bash
git clone https://github.com/agitter/spras.git
git checkout -b local-neighborhood
```
Then you can make commits and push them to your fork of the repository on the `local-neighborhood` branch
```bash
git push origin local-neighborhood
```
For this local neighborhood example only, you will not merge the changes back to the original SPRAS repository.
Instead, you can open a pull request to your fork so that the SPRAS maintainers can still provide feedback.
For example, use the "New pull request" button from <https://github.com/agitter/spras/pulls> and set `agitter/spras` as both the base repository and the head repository with `local-neighborhood` as the compare branch.

An alternative way to set up SPRAS for local development is to  clone the Reed-CompBio version of the repository to your local machine and add your fork as another git remote so your can push changes to both.
```bash
git clone https://github.com/Reed-CompBio/spras.git
git remote add agitter https://github.com/agitter/spras.git
git remote -v
```
The second line adds a new remote named `agitter` in addition to the default `origin` remote.
Then it is possible to push commits to `origin` or `agitter`.
This provides more flexibility.
The third line shows all available remotes.

With this configuration, you push commits to your fork and then make a pull request to your fork as above, except now the remote has a different name.
```bash
git push agitter local-neighborhood
```

### Step 1: Practice with the Local Neighborhood algorithm
The Local Neighborhood pathway reconstruction is implemented and described in the [`docker-wrappers/LocalNeighborhood`](docker-wrappers/LocalNeighborhood) directory.
The readme in that directory describes the usage and the three required arguments.
This algorithm does not require any third-party packages, only Python 3.x.
Run `local_neighborhood.py` from the command line.
There are example input files `ln-network.txt` and `ln-nodes.txt` in [`test/LocalNeighborhood/input`](test/LocalNeighborhood/input).
Copy them to the `LocalNeighborhood` directory for testing.
Confirm that the output file matches expectations.

### Step 2: Create a Local Neighborhood Docker image
Complete the `Dockerfile` in the [`docker-wrappers/LocalNeighborhood`](docker-wrappers/LocalNeighborhood) directory to create a Docker image.
The PathLinker `Dockerfile` demonstrates how to begin with a Python image and copy files into the image with `COPY`.
Browse the official [Python images](https://hub.docker.com/_/python) to select a recent version of Python based on Alpine Linux, a small Linux distribution.
Note that the PathLinker example uses an old version of Python, but this Local Neighborhood Docker image should be based on a more modern version of Python.
In addition, not all pathway reconstruction algorithms are compatible with Alpine Linux, so the default Debian-based Python image is required.
The `Dockerfile` does not need an `ENTRYPOINT` or `CMD` line.
It will be used to run a Python command.

Build the Docker image by running
```
docker build -t <username>/local-neighborhood -f Dockerfile .
```
from the `LocalNeighborhood` directory, where `<username>` is your Docker Hub username.
Docker must be running on your system before executing this command.

Test the image by running it with the example input files
```
docker run -w /data --mount type=bind,source=/${PWD},target=/data \
  <username>/local-neighborhood python local_neighborhood.py \
  --network /data/ln-network.txt --nodes /data/ln-nodes.txt \
  --output /data/ln-output.txt
```
This will mount the current working directory to the directory `/data` inside the container so that the input files can be read and the output file can be written.
It will set the working directory inside the container to `/data`.
`<username>/local-neighborhood` specifies which container to run the command in.

The parts of the command starting with `python` are the command run inside the container, which is why the file paths like `/data/ln-network.txt` are relative to the container's file system instead of your local file system.
The command assumes the test files have already been copied into the current working directory.
Windows users may need to escape the absolute paths so that `/data` becomes `//data`, etc.
Confirm that the output file matches expectations.

Push the new image to Docker Hub:
```
docker push <username>/local-neighborhood
```
Pushing an image requires being logged in, so run `docker login` first if needed using your Docker Hub username and password.

### Step 3: Write the Local Neighborhood wrapper functions
Add a new Python file `src/local_neighborhood.py` to implement the wrapper functions for the Local Neighborhood algorithm.
Use `pathlinker.py` as an example.

Call the new class within `local_neighborhood.py` `LocalNeighborhood` and set `__all__` so the class can be [imported](https://docs.python.org/3/tutorial/modules.html#importing-from-a-package).
Specify the list of `required_input` files to be `network` and `nodes`.
These entries are used to tell Snakemake what input files should be present before running the Local Neighborhood algorithm.

Before implementing the `generate_inputs` function, explore the structure of the `Dataset` class interactively.
In an interactive Python session, run the following commands to load the `data0` dataset and explore the nodes and interactome.
```python
> from src.dataset import Dataset
> dataset_dict = {'label': 'data0', 'node_files': ['node-prizes.txt', 'sources.txt', 'targets.txt'], 'edge_files': ['network.txt'], 'other_files': [], 'data_dir': 'input'}
> data = Dataset(dataset_dict)
> data.node_table.head()
  NODEID  prize active sources targets
0      C    5.7   True     NaN    True
1      A    2.0   True    True     NaN
2      B    NaN    NaN     NaN     NaN
> data.interactome.head()
  Interactor1 Interactor2  Weight
0           A           B    0.98
1           B           C    0.77
```
Also test the functions available in the `Dataset` class.
```python
> data.request_node_columns(['sources'])
  sources NODEID
0    True      A
```
Note the behaviors of the `request_node_columns` function when there are missing values in that column of the node table and when multiple columns are requested.
`request_node_columns` always returns the `NODEID` column in addition to the requested columns.

Now implement the `generate_inputs` function, following the `omicsintegrator1.py` example.
The selected nodes should be any node in the dataset that has a prize set, any node that is active, any node that is a source, or any node that is a target.
As shown in the example dataset above, "active", "sources", and "targets" are Boolean attributes.
A "prize" is a term for a numeric score on a node in a network, so nodes that have non-empty prizes are considered relevant nodes for the Local Neighborhood algorithm along with active nodes, sources, and targets.
The network should be all of the edges written in the format `<vertex1>|<vertex2>`.
`src/dataset.py` provides functions that provide access to node information and the interactome (edge list).

Implement the `run` function, following the PathLinker example.
The `prepare_volume` utility function is needed to prepare the network and nodes input files to be mounted and used inside the container.
It is also used to prepare the path for the output file, which is different from how the output is prepared in the PathLinker example.
The functionality of `prepare_volume` is similar to how you had to manually specify paths relative to the container's file system when you interactive tested the container in Step 2.
It is not necessary to create the output directory in advance because the Local Neighborhood algorithm will create it if it does not exist.

Prepare the command to run inside the container, which will resemble the command used when running Local Neighborhood in Step 1.
Use the `run_container` utility function to run the command in the container `<username>/local-neighborhood` that was pushed to Docker Hub in Step 2.

Implement the `parse_output` function.
The edges in the Local Neighborhood output have the same format as the input, `<vertex1>|<vertex2>`.
Convert these to be tab-separated vertex pairs followed by a tab and a `1` at the end of every line, which indicates all edges have the same rank.
See the `add_rank_column` function in `src.util.py`.
The output should have the format `<vertex1> <vertex2> 1`.

### Step 4: Make the Local Neighborhood wrapper accessible through SPRAS
Import the new class `LocalNeighborhood` in `src/runner.py` so the wrapper functions can be accessed.
Add an entry for Local Neighborhood to the configuration file `config/config.yaml` and set `include: true`.
As a convention, algorithm names are written in all lowercase without special characters.
Local Neighborhood has no other parameters.
Optionally set `include: false` for the other pathway reconstruction algorithms to make testing faster.

After completing this step, try running the Local Neighborhood algorithm through SPRAS with
```bash
snakemake --cores 1 --configfile config/config.yaml
```
Make sure to run the command inside the `spras` conda environment. If installing via `pip` instead of using conda, install with the `-e .[dev]` options (the full command to run from the repo root is `python -m pip install -e .[dev]`) so that Python picks up any changes you make and installs all optional development packages. Omitting the `-e` flag will prevent your changes from being reflected unless you force re-install, and omitting `.[dev]` will prevent pip from installing `pre-commit` and `pytest`.

As a workflow manager, Snakemake will consider the work described in the configuration file to be completed once the necessary output files have been written to the relevant output directory (`output` in the `config/config.yaml` configuration).
That means that if you change your code and rerun the Snakemake command above, nothing may happen if the output files already exist.
To iteratively update code and test the workflow, you typically have to remove the output directory or all of its contents before rerunning the Snakemake command.

### Step 5: Add Local Neighborhood to the tests
Add test functions to the test file `test/test_ln.py`.
This file already has existing tests to test the correctness of the Local Neighborhood implementation that was added to the Docker image.
The new tests will test that the `run` function of the `LocalNeighborhood` class works correctly.
Use `test_pathlinker.py` as an example.
There are input files for testing in the [`test/LocalNeighborhood/input`](test/LocalNeighborhood/input) directory.
The new test functions will be automatically run as part of the pytest testing.

Extend `.github/workflows/test-spras.yml` to pull and build the new Docker image.
Follow the example for any of the other pathway reconstruction algorithm.
First pull the image `<username>/local-neighborhood` from Docker Hub.
Then build the Docker image using the `Dockerfile` that was completed in Step 2.

Modify generate inputs:
1. Include a key-value pair in the algo_exp_file dictionary that links the specific algorithm to its expected network file.
2. Obtain the expected network file from the workflow, manually confirm it is correct, and save it to `test/generate-inputs/expected`. Name it as `{algorithm_name}-{network_file_name}-expected.txt`.

Modify parse outputs:
1. Obtain the raw-pathway output (e.g. from the run function in your wrapper by running the Snakemake workflow) and save it to `test/parse-outputs/input`. Name it as `{algorithm_name}-raw-pathway.txt`.
2. Obtain the expected universal output from the workflow, manually confirm it is correct, and save it to `test/parse-outputs/expected` directory. Name it as `{algorithm_name}-pathway-expected.txt`.
3. Add the new algorithm's name to the algorithms list in `test/parse-outputs/test_parse_outputs.py`.

### Step 6: Work with SPRAS maintainers to revise the pull request
Step 0 previously described how to create a `local-neighborhood` branch and create a pull request.
Make sure to commit all of the new and modified files and push them to the `local-neighborhood` branch on your fork.

The SPRAS maintainers will review the pull request and provide feedback and suggested changes.
If you are not already in communication with them, you can open a [GitHub issue](https://github.com/Reed-CompBio/spras/issues/new/choose) to request feedback.
However, once the pull request has been approved, it will **not** be merged as usual.
The pull request will be closed so that the `master` branch of the fork stays synchronized with the `master` branch of the main SPRAS repository.

## General steps for contributing a new pathway reconstruction algorithm
1. Open a [GitHub issue](https://github.com/Reed-CompBio/spras/issues/new/choose) to propose adding a new algorithm and discuss it with the SPRAS maintainers
1. Add a new subdirectory to `docker-wrappers` with the name `<algorithm>`, write a `Dockerfile` to build an image for `<algorithm>`, and include any other files required to build that image in the subdirectory
1. Build and push the Docker image to the [reedcompbio](https://hub.docker.com/orgs/reedcompbio) Docker organization (SPRAS maintainer required)
1. Add a new Python file `src/<algorithm>.py` to implement the wrapper functions for `<algorithm>`: specify the list of `required_input` files and the `generate_inputs`, `run`, and `parse_output` functions
1. Import the new class in `src/runner.py` so the wrapper functions can be accessed
1. Document the usage of the Docker wrapper and the assumptions made when implementing the wrapper
1. Add example usage for the new algorithm and its parameters to the template config file
1. Write test functions and provide example input data in a new test subdirectory `test/<algorithm>`. Provide example data and algorithm/expected files names to lists or dicts in `test/generate-inputs` and `test/parse-outputs`. Use the full path with the names of the test files.
1. Extend `.github/workflows/test-spras.yml` to pull and build the new Docker image

When adding new algorithms, there are many other considerations that are not relevant with the simple Local Neighborhood example.
Most algorithms require dependencies that need to be installed in the `Dockerfile`.
See the linked Carpentries Docker introduction above for instructions on creating a `Dockerfile` and the `OmicsIntegrator1` example for an example of specifying Python dependencies.

Some algorithms may be custom implementations that are not available and maintained elsewhere.
In that case, create a separate repository for the core pathway reconstruction algorithm source code and download it into the Docker image.
See the `MinCostFlow` example.
Note that when downloading code directly from GitHub that does not have versioned releases, it is recommended to specify a git commit hash.

## Pre-commit hooks
SPRAS uses [pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks) to automatically catch certain types of formatting and programming errors in source files.
Example errors include a yaml file that cannot be parsed or a local variable that is referenced before assignment.
These tests are run automatically on every commit through the GitHub Actions.
However, developers will benefit from setting up their environment to run the same tests locally while they modify the SPRAS source.

The `pre-commit` package is installed as part of the conda environment in `environment.yml`, or when installing SPRAS with `python -m pip install -e .[dev]`.
From there, the pre-commit [quick start](https://pre-commit.com/#quick-start) guide explains two primary ways to use it locally:
- run against all source files with `pre-commit run --all-files` to identify errors and automatically fix them when possible
- configure `git` to run the hooks before every `git commit` so that a commit will only succeed if the tests pass, ensuring new errors are not introduced

Currently, SPRAS only enforces a small number of Python formatting conventions and runs a small number of tests.
Additional hooks are [available](https://github.com/pre-commit/pre-commit-hooks#hooks-available).
These are configured in `.pre-commit-config.yaml`.
SPRAS also runs [`ruff`](https://github.com/charliermarsh/ruff) as part of the pre-commit hooks to perform the Python code analysis, which supports many more [rules](https://beta.ruff.rs/docs/rules/).
These are configured in `pyproject.toml`.
