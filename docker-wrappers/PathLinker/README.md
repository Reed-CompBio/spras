# PathLinker Docker image

A Docker image for [PathLinker](https://github.com/Murali-group/PathLinker) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/pathlinker).

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t reedcompbio/pathlinker -f Dockerfile .
```
from this directory.

To confirm that commands are run inside the conda environment run:
```
winpty docker run reedcompbio/pathlinker conda list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/PathLinker`.
The `input` subdirectory contains test files `sample-in-net.txt` and `sample-in-nodetypes.txt`.
The Docker wrapper can be tested with `pytest`.

## TODO
- Attribute https://github.com/Murali-group/PathLinker
- Document usage
- Consider `continuumio/miniconda3:4.9.2-alpine` base image
