# Docker tests

This subdirectory contains examples of using Docker's Python API https://github.com/docker/docker-py.
It the SINGE [example data](https://github.com/gitter-lab/SINGE/tree/master/data1) and [Docker image](https://hub.docker.com/r/agitter/singe) with a reduced set of hyperparamters.
The docker-py API is more readable than the similar [BEELINE Docker command](https://github.com/Murali-group/Beeline/blob/7f6e07a3cb784227bf3fa889fe0c36e731c22c5c/BLRun/singeRunner.py#L110-L116) and most likely also more robust across different operating systems.

## Installation

Install docker-py with the command `pip install docker`.

The Docker client must be installed separately.

## Usage

Before running `docker-demo.py`, start the Docker client and install the `docker` Python package.
Then, from this `docker` directory run the command:
```
python docker-demo.py
```

SINGE will run inside Docker, which takes a few minutes.
The output files will be written to the `output` subdirectory.

If the Docker image `agitter/singe:0.4.1` is not already available locally, the script will automatically pull it from [DockerHub](https://hub.docker.com/r/agitter/singe).

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t conda-test/conda-test -f Dockerfile .
```

To confirm that commands are run inside the conda environment run:
```
winpty docker run conda-test/conda-test conda list
winpty docker run conda-test/conda-test python -c "import networkx; print(networkx.__version__)"
```
The `winpty` prefix is only needed on Windows.
