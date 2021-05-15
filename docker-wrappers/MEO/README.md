# Maximum Edge Orientation Docker image

A Docker image for [Maximum Edge Orientation](https://github.com/agitter/meo/).

## Building the Docker image

To create the Docker image run:
```
docker build -t reedcompbio/meo -f Dockerfile .
```
from this directory.
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/meo`.
The `input` subdirectory contains test files `sample-edges.txt`, `sample-sources.txt`, and `sample-targets.txt`.
The Docker wrapper can be tested with `pytest`.

## TODO
- https://github.com/agitter/meo/
- Document usage
- Consider Alpine-based base image
