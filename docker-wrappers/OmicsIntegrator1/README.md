# Omics Integrator 1 Docker image

A Docker image for [Omics Integrator](https://github.com/fraenkel-lab/OmicsIntegrator) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/omics-integrator-1).

## Building and testing

To create the Docker image run:
```
docker build -t reedcompbio/omics-integrator-1 -f Dockerfile .
```
from this directory.

Test code is located in `test/OmicsIntegrator1`.
The `input` subdirectory contains test files `oi1-edges.txt`, `oi1-prizes.txt`, and `oi1-dummy.txt`.
The Docker image can be tested with `pytest`.

The Docker image also can be tested by running the Omics Integrator tests interactively:
```
docker run -it reedcompbio/omics-integrator-1 bash
python setup.py test -a "--msgpath=$MSGSTEINER_PATH"
```

## Versions:
- v1: Created a named conda environment in the container and used `ENTRYPOINT` to execute commands inside that environment. Not compatible with Singularity.
- no-conda: Avoided conda and used a Python 2.7.18 base image to install the required Python dependencies.
- v2: Installed Python 2.7.18 and all dependencies into a Debian slim image.

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator
- Attribute http://staff.polito.it/alfredo.braunstein/code/msgsteiner-1.3.tgz and discuss permission to distribute
- Optimize order of commands in Dockerfile
- Delete data files
- Document usage
- Remove testing and setup packages from environment if not needed
- Determine how to use MSGSTEINER_PATH when passing in commands, fix ENTRYPOINT and/or CMD
- Decide what to use for working directory and where to map input data
