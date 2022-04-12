# PathLinker Docker image

A Docker image for [PathLinker](https://github.com/Murali-group/PathLinker) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/pathlinker).

To create the Docker image run:
```
docker build -t reedcompbio/pathlinker -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run reedcompbio/pathlinker pip list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/PathLinker`.
The `input` subdirectory contains test files `sample-in-net.txt` and `sample-in-nodetypes.txt`.
The Docker wrapper can be tested with `pytest`.

## TODO
- Attribute https://github.com/Murali-group/PathLinker
- Document usage
