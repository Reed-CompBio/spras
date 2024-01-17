# Cytoscape image

A Docker image for [Cytoscape](https://cytoscape.org/) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/py4cytoscape).
It was originally derived from the [`docker-cytoscape-desktop/py4cytoscape`](https://github.com/cytoscape/docker-cytoscape-desktop/blob/173ab46b4b5e5c148113ad0c9960a6af3fc50432/py4cytoscape/Dockerfile) image.

Thank you to Scooter Morris for help debugging problems running Cytoscape in Singularity.

## Building the Docker image

To create the Docker image run:
```
docker build -t reedcompbio/py4cytoscape -f Dockerfile .
```
from this directory.

## Testing
Test code is located in `test/analysis/test_cytoscape.py`.
The Docker wrapper can be tested with `pytest`.

## Versions:
- v1: Use supervisord to launch Cytoscape from a Python subprocess, then connect to Cytoscape with py4cytoscape. Only loads undirected pathways. Compatible with Singularity in local testing (Apptainer version 1.2.2-1.el7) but fails in GitHub Actions.
- v2: Add support for edge direction column.

## TODO
- Add an auth file for `xvfb-run`
- Java initial heap size, maximum Java heap size, and thread stack size are hard-coded in `Cytoscape.vmoptions` file
- Resolve issues with `Cytoscape.vmoptions` line endings being reset to Windows-style. They must be reset periodically, and the image will fail if they are not Unix-style.
