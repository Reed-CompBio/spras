# Omics Integrator 2 Docker image

A Docker image for [Omics Integrator 2](https://github.com/fraenkel-lab/OmicsIntegrator2).

## Activating conda inside a Docker container

By default, an installed conda environment will not be activated inside the Docker container.
Docker does not invoke Bash as a login shell.
[This blog post](https://pythonspeed.com/articles/activate-conda-dockerfile/) provides a workaround demonstrated here in `Dockerfile` and `env.yml`.
It defines a custom ENTRYPOINT that uses `conda run` to run the command inside the conda environment.

To create the Docker image run:
```
docker build -t agitter/omics-integrator-2 -f Dockerfile .
```

To confirm that commands are run inside the conda environment run:
```
winpty docker run agitter/omics-integrator-2 conda list
winpty docker run agitter/omics-integrator-2 OmicsIntegrator
```
The `winpty` prefix is only needed on Windows.

## TODO
- Attribute https://github.com/fraenkel-lab/OmicsIntegrator2
- Modify environment to use fraenkel-lab or [PyPI](https://pypi.org/project/OmicsIntegrator/) version instead of fork