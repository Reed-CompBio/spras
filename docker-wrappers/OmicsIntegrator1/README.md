# Omics Integrator 1 Docker image

A Docker image for [Omics Integrator](https://github.com/fraenkel-lab/OmicsIntegrator).

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t agitter/omics-integrator-1 -f Dockerfile .
```

To confirm that commands are run inside the conda environment run:
```
winpty docker run agitter/omics-integrator-1 conda list
```
The `winpty` prefix is only needed on Windows.

## Testing
The `input` directory contains test files `oi1-edges.txt` and `oi2-prizes.txt`.
The Docker wrapper can be tested with the command
```
python test-oi1.py
```

The Docker wrapper also can be tested by running the Omics Integrator tests interactively:
```
winpty docker run -it agitter/omics-integrator-1 bash
conda activate oi1
python setup.py test -a "--msgpath=$MSGSTEINER_PATH"
```

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator
- Attribute http://staff.polito.it/alfredo.braunstein/code/msgsteiner-1.3.tgz and discuss permission to distribute
- Optimize order of commands in Dockerfile
- Delete data files
- Document usage
- Remove testing and setup packages from environment if not needed
- Determine how to use MSGSTEINER_PATH when passing in commands, fix ENTRYPOINT and/or CMD
- Decide what to use for working directory and where to map input data
- Consider `continuumio/miniconda3:4.9.2-alpine` base image
