# Omics Integrator 2 Docker image

A Docker image for [Omics Integrator 2](https://github.com/fraenkel-lab/OmicsIntegrator2) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/omics-integrator-2).

## Building the Docker image

To create the Docker image run:
```
docker build -t reedcompbio/omics-integrator-2 -f Dockerfile .
```
from this directory.

To confirm that commands are run inside the conda environment run:
```
winpty docker run reedcompbio/omics-integrator-2 conda list
winpty docker run reedcompbio/omics-integrator-2 OmicsIntegrator -h
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/OmicsIntegrator2`.
The `input` subdirectory contains test files `oi2-edges.txt` and `oi2-prizes.txt`.
The Docker wrapper can be tested with `pytest`.

## Versions:
- v1: Created a named conda environment in the container and used `ENTRYPOINT` to execute commands inside that environment. Not compatible with Singularity.
- v2: Used the environment file to update the base conda environment so the `ENTRYPOINT` command was no longer needed. Compatible with Singularity.

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator2
- Modify environment to use fraenkel-lab or [PyPI](https://pypi.org/project/OmicsIntegrator/) version instead of fork
- Document usage
