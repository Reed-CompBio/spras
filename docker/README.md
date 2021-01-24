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
