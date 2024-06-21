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

Alternatively, to test the Docker image directly, run the following command from the root of the `spras` repository
```
docker run -w /data --mount type=bind,source=/${PWD},target=/data reedcompbio/pathlinker python /PathLinker/run.py \
  /data/test/PathLinker/input/sample-in-net.txt /data/test/PathLinker/input/sample-in-nodetypes.txt -k 5 --write-paths
```
This will run PathLinker on the test input files and write the output files to the root of the `spras` repository.
Windows users may need to escape the absolute paths so that `/data` becomes `//data`, etc.

## Versions:
- v1: Initial version. Copies PathLinker source files from GitHub and pip installs packages from requirements file.
- v2: Add bash, which is not available in Alpine Linux.

## TODO
- Attribute https://github.com/Murali-group/PathLinker
- Document usage
