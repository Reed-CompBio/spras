# SPRAS Docker image

## Building
A Docker image for SPRAS that is available on [Dockerhub]()
This image comes bundled with all of the necessary software packages to run SPRAS, and can be used for execution in distributed environments (like HTCondor).

To create the Docker image, make sure you are in this repository's root directory, and from your terminal run:
```
docker build -t reedcompbio/spras -f docker-wrappers/SPRAS/Dockerfile .
```

This will copy the entire SPRAS repository into the container and install SPRAS with `pip`. As such, any changes you've made to the current SPRAS repository will be reflected in version of SPRAS installed in the container. Since SPRAS
is being installed with `pip`, it's also possible to specify that you want development modules installed as well. If you're using the container for development and you want the optional `pre-commit` and `pytest` packages as well as a
spras package that receives changes without re-installation, change the
`pip` installation line to:
```
pip install -e .[dev]
```
This will cause changes to spras source code to update the intsalled package.

**Note:** This image will build for the same platform that is native to your system (ie amd64 or arm64). If you need to run this in a remote environment like HTCondor that is almost certainly `amd64` but you're building from Apple Silicon, it is recommended to either modify the Dockerfile to pin the platform:
```
FROM --platform=linux/amd64 almalinux:9
```

Or to temporarily override your system's default by exporting the environment variable:
```
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```
(This environment variable can then be cleared by running `unset DOCKER_DEFAULT_PLATFORM` to return your system to its default)


## Testing

The folder `docker-wrappers/SPRAS` also contains several files that can be used to test this container on HTCondor.
