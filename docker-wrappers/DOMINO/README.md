# DOMINO Docker image

A Docker image for [DOMINO](https://github.com/Shamir-Lab/DOMINO) that is available on [DockerHub](https://hub.docker.com/repository/docker/otjohnson/domino).

DOMINO outputs multiple active modules, which SPRAS combines into a single pathway.

To create the Docker image run:
```
docker build -t otjohnson/domino -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run otjohnson/domino pip list
```
The `winpty` prefix is only needed on Windows.
