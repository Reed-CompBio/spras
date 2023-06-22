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

It is not necessary to have experience with Snakemake or Python testing before getting started, but it may help with more complex SPRAS contributions:
- Snakemake [Carpentries introduction](https://carpentries-incubator.github.io/workflows-snakemake/) or [beginner's guide](http://ivory.idyll.org/blog/2023-snakemake-slithering-section-1.html)
- pytest [getting started](https://docs.pytest.org/en/7.1.x/getting-started.html) and [how-to guides](https://docs.pytest.org/en/7.1.x/how-to/index.html)

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

Implement the `generate_inputs` function, following the `omicsintegrator1.py` example.
The nodes should be any node in the dataset that has a prize set, any node that is a source, or any node that is a target.
The network should be all of the edges written in the format `<vertex1>|<vertex2>`.
`src/dataset.py` provides functions that provide access to node information and the interactome (edge list).

Implement the `run` function, following the Path Linker example.
The `prepare_volume` utility function is needed to prepare the network and nodes input files to be mounted and used inside the container.
It is also needed to prepare the path for the output file.
This is similar to how you had to manually specify paths relative to the container's file system when you interactive tested the container in Step 2.
It is not necessary to create the output directory in advance because the Local Neighborhood algorithm will create it if it does not exist.

Prepare the command to run inside the container, which will resemble the command used when running Local Neighborhood in Step 1.
Use the `run_container` utility function to run the command in the container `<username>/local-neighborhood` that was pushed to Docker Hub in Step 2.

Implement the `parse_output` function.
The edges in the Local Neighborhood output have the same format as the input, `<vertex1>|<vertex2>`.
Convert these to be tab-separated vertex pairs followed by a tab and a `1` at the end of every line, which indicates all edges have the same rank.
The output should have the format `<vertex1> <vertex2> 1`.

### Step 4: Make the Local Neighborhood wrapper accessible through SPRAS
Import the new class `LocalNeighborhood` in `PRRunner.py` so the wrapper functions can be accessed.
Add an entry for Local Neighborhood to the configuration file `config/config.yaml` and set `include: true`.
Local Neighborhood has no other parameters.
Optionally set `include: false` for the other pathway reconstruction algorithms to make testing faster.

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

### Step 6: Create a pull request to add Local Neighborhood to the SPRAS repository
These instructions assume the `spras` repository has already been cloned locally and the contributor has their own fork that has been added as a remote.
Create a new branch in the `spras` repository:
```
git checkout -b local-neighborhood
```
Commit all of the new and modified files.
It may be preferable to make several smaller commits while working on Steps 1 through 5 instead of waiting to commit them all in Step 6.
Push the branch to the contributor's fork.
Visit <https://github.com/Reed-CompBio/spras/pulls> to create a new pull request.
The SPRAS maintainers will review the pull request and provide feedback and suggested changes.
However, once the pull request has been approved, it will **not** be merged as usual.
The pull request will be closed so that future contributors can practice with the Local Neighborhood algorithm.

## Contributing a new pathway reconstruction algorithm summary
1. Open a [GitHub issue](https://github.com/Reed-CompBio/spras/issues/new/choose) to propose adding a new algorithm and discuss it with the SPRAS maintainers
1. Add a new subdirectory to `docker-wrappers` with the name `<algorithm>`, write a `Dockerfile` to build an image for `<algorithm>`, and include any other files required to build that image in the subdirectory
1. Build and push the Docker image to the [reedcompbio](https://hub.docker.com/orgs/reedcompbio) Docker organization (SPRAS maintainer required)
1. Add a new Python file `src/<algorithm>.py` to implement the wrapper functions for `<algorithm>`: specify the list of `required_input` files and the `generate_inputs`, `run`, and `parse_output` functions
1. Import the new class in `runner.py` so the wrapper functions can be accessed
1. Document the usage of the Docker wrapper and the assumptions made when implementing the wrapper
1. Add example usage for the new algorithm and its parameters to the template config file
1. Write test functions and provide example input data in a new test subdirectory `test/<algorithm>`
1. Extend `.github/workflows/test-spras.yml` to pull and build the new Docker image

## Pre-commit hooks
SPRAS uses [pre-commit hooks](https://github.com/pre-commit/pre-commit-hooks) to automatically catch certain types of formatting and programming errors in source files.
Example errors include a yaml file that cannot be parsed or a local variable that is referenced before assignment.
These tests are run automatically on every commit through the GitHub Actions.
However, developers will benefit from setting up their environment to run the same tests locally while they modify the SPRAS source.

The `pre-commit` package is installed as part of the conda environment in `environment.yml`.
From there, the pre-commit [quick start](https://pre-commit.com/#quick-start) guide explains two primary ways to use it locally:
- run against all source files with `pre-commit run --all-files` to identify errors and automatically fix them when possible
- configure `git` to run the hooks before every `git commit` so that a commit will only succeed if the tests pass, ensuring new errors are not introduced

Currently, SPRAS only enforces a small number of Python formatting conventions and runs a small number of tests.
Additional hooks are [available](https://github.com/pre-commit/pre-commit-hooks#hooks-available).
These are configured in `.pre-commit-config.yaml`.
SPRAS also runs [`ruff`](https://github.com/charliermarsh/ruff) as part of the pre-commit hooks to perform the Python code analysis, which supports many more [rules](https://beta.ruff.rs/docs/rules/).
These are configured in `pyproject.toml`.
