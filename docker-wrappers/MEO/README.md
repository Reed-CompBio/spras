# Maximum Edge Orientation Docker image

A Docker image for [Maximum Edge Orientation](https://github.com/agitter/meo/) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/meo).
Only supports the Random orientation algorithm, not MINSAT or MAXCSP.

## Building the Docker image

To create the Docker image run:
```
docker build -t reedcompbio/meo -f Dockerfile .
```
from this directory.

## Testing
Test code is located in `test/meo`.
The `input` subdirectory contains test files `meo-edges.txt`, `meo-sources.txt`, and `meo-targets.txt`.
The Docker wrapper can be tested with `pytest`.

## TODO
- Attribute https://github.com/agitter/meo/
- Document usage
- Consider Alpine-based base image
