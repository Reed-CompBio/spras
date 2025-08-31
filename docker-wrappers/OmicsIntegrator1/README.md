# Omics Integrator 1 Docker image

A Docker image for [Omics Integrator](https://github.com/fraenkel-lab/OmicsIntegrator) that is available on the [GitHub Container Registry](https://github.com/orgs/Reed-CompBio/packages/container/package/omics-integrator-1).

To create the Docker image run:
```
docker build -t reed-compbio/omics-integrator-1 -f Dockerfile .
```
from this directory.

To confirm that commands are run inside the conda environment run:
```
winpty docker run reed-compbio/omics-integrator-1 conda list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/OmicsIntegrator1`.
The `input` subdirectory contains test files `oi1-edges.txt` and `oi1-prizes.txt`.
The Docker wrapper can be tested with `pytest`.

The Docker wrapper also can be tested by running the Omics Integrator tests interactively:
```
winpty docker run -it reed-compbio/omics-integrator-1 bash
python setup.py test -a "--msgpath=$MSGSTEINER_PATH"
```

## Versions

- v1: Initial OmicsIntegrator1 from the [original no-conda image](https://github.com/Reed-CompBio/spras/blob/fad9fbf782ae0bd1e0cf660b7ef2a2d61df41cf5/docker-wrappers/OmicsIntegrator1/Dockerfile_no_conda)
- v2: Updated the base image and manually installed python.

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
