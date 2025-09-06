# Omics Integrator 1 Docker image

A Docker image for [Omics Integrator](https://github.com/fraenkel-lab/OmicsIntegrator) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/omics-integrator-1).

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t reedcompbio/omics-integrator-1 -f Dockerfile .
```
from this directory.

To confirm that commands are run inside the conda environment run:
```
winpty docker run reedcompbio/omics-integrator-1 conda list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/OmicsIntegrator1`.
The `input` subdirectory contains test files `oi1-edges.txt` and `oi1-prizes.txt`.
The Docker wrapper can be tested with `pytest`.

The Docker wrapper also can be tested by running the Omics Integrator tests interactively:
```
winpty docker run -it reedcompbio/omics-integrator-1 bash
conda activate oi1
python setup.py test -a "--msgpath=$MSGSTEINER_PATH"
```

## Versions:
- v1: Created a named conda environment in the container and used `ENTRYPOINT` to execute commands inside that environment. Not compatible with Singularity.
- no-conda: Avoided conda and used a Python 2.7.18 base image to install the required Python dependencies.
- v2: Installed Python 2.7.18 and all dependencies into a Debian slim image.

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator
- Attribute http://staff.polito.it/alfredo.braunstein/code/msgsteiner-1.3.tgz and discuss permission to distribute
- Optimize order of commands in Dockerfile
- Delete data files
- Document usage
- Remove testing and setup packages from environment if not needed
- Determine how to use MSGSTEINER_PATH when passing in commands, fix ENTRYPOINT and/or CMD
- Decide what to use for working directory and where to map input data
- Consider Alpine base image
