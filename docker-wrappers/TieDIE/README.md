# TieDIE Docker image

A Docker image for [TieDIE](https://github.com/epaull/TieDIE) that is available on [DockerHub](https://hub.docker.com/r/erikliu24/tiedie).

To create the Docker image run:
```
docker build -t erikliu24/tiedie -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run reedcompbio/pathlinker pip list
```
The `winpty` prefix is only needed on Windows.

## TODO
- How to run
- Test
