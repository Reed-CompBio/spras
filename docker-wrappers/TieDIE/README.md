# TieDIE Docker image

A Docker image for [TieDIE](https://github.com/epaull/TieDIE) that is available on [DockerHub](https://hub.docker.com/r/erikliu24/tiedie).

To create the Docker image run:
```
docker build -t erikliu24/tiedie -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run erikliu24/tiedie pip list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/TieDIE`.
The `input` subdirectory contains test files `pathway.txt`, `target.txt` and `source.txt`.
The Docker wrapper can be tested with `pytest` or a unit test with `pytest -k test_rwr.py`.