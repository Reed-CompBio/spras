# Cytoscape image

A Docker image for [Cytoscape](https://cytoscape.org/) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/py4cytoscape).
It was originally derived from the [`docker-cytoscape-desktop/py4cytoscape
`](https://github.com/cytoscape/docker-cytoscape-desktop/blob/173ab46b4b5e5c148113ad0c9960a6af3fc50432/py4cytoscape/Dockerfile) image.

## Building the Docker image

To create the Docker image run:
```
docker build -t reedcompbio/py4cytoscape -f Dockerfile .
```
from this directory.

This Docker image is compatible with Docker but not yet Singularity.

## TODO
- Finish this readme
- Add an auth file for `xvfb-run`
- Java initial heap size, maximum Java heap size, and thread stack size are hard-coded in `Cytoscape.vmoptions` file
