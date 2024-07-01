# SPRAS Docker image

## Building

A Docker image for SPRAS that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/spras)
This image comes bundled with all of the necessary software packages to run SPRAS, and can be used for execution in distributed environments (like HTCondor).

To create the Docker image, make sure you are in this repository's root directory, and from your terminal run:

```
docker build -t <project name>/<image name>:<tag name> -f docker-wrappers/SPRAS/Dockerfile .
```

For example, to build this image with the intent of pushing it to DockerHub as reedcompbio/spras:v0.1.0, you'd run:
```
docker build -t reedcompbio/spras:v0.1.0 -f docker-wrappers/SPRAS/Dockerfile .
```

This will copy the entire SPRAS repository into the container and install SPRAS with `pip`. As such, any changes you've made to the current SPRAS repository will be reflected in version of SPRAS installed in the container. Since SPRAS
is being installed with `pip`, it's also possible to specify that you want development modules installed as well. If you're using the container for development and you want the optional `pre-commit` and `pytest` packages as well as a
spras package that receives changes without re-installation, change the
`pip` installation line to:

```
pip install -e .[dev]
```

This will cause changes to spras source code to update the installed package.

**Note:** This image will build for the same platform that is native to your system (i.e. amd64 or arm64). If you need to run this in a remote environment like HTCondor that is almost certainly `amd64` but you're building from Apple Silicon, it is recommended to either modify the Dockerfile to pin the platform:

```
FROM --platform=linux/amd64 almalinux:9
```

Or to temporarily override your system's default during the build, prepend your build command with:
```
DOCKER_DEFAULT_PLATFORM=linux/amd64
```

For example, to build reedcompbio/spras:v0.1.0 on Apple Silicon as a linux/amd64 container, you'd run:
```
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker build -t reedcompbio/spras:v0.1.0 -f docker-wrappers/SPRAS/Dockerfile .
```

## Testing

The folder `docker-wrappers/SPRAS` also contains several files that can be used to test this container on HTCondor. To test the `spras` container
in this environment, first login to an HTCondor Access Point (AP). Then, from the AP clone this repo:

```
git clone https://github.com/Reed-CompBio/spras.git
```

When you're ready to run SPRAS as an HTCondor workflow, navigate to the `spras/docker-wrappers/SPRAS` directory and create the `logs/` directory. Then run
`condor_submit spras.sub`, which will submit SPRAS to HTCondor as a single job with as many cores as indicated by the `NUM_PROCS` line in `spras.sub`, using
the value of `EXAMPLE_CONFIG` as the SPRAS configuration file. Note that you can alter the configuration file to test various workflows, but you should leave
`unpack_singularity = true`, or it is likely the job will be unsuccessful. By default, the `example_config.yaml` runs everything except for `cytoscape`, which
appears to fail periodically in HTCondor.

To monitor the state of the job, you can run `condor_q` for a snapshot of how the job is doing, or you can run `condor_watch_q` if you want realtime updates.
Upon completion, the `output` directory from the workflow should be returned as `spras/docker-wrappers/SPRAS/output`, along with several files containing the
workflow's logging information (anything that matches `logs/spras_*` and ending in `.out`, `.err`, or `.log`). If the job was unsuccessful, these files should
contain useful debugging clues about what may have gone wrong.

**Note**: If you want to run the workflow with a different version of SPRAS, or one that contains development updates you've made, rebuild this image against
the version of SPRAS you want to test, and push the image to your image repository. To use that container in the workflow, change the `container_image` line of
`spras.sub` to point to the new image.

**Note**: In some cases, especially if you're encountering an error like `/srv//spras.sh: line 10: snakemake: command not found`, it may be necessary to convert
the SPRAS image to a `.sif` container image before running someplace like the OSPool. To do this, run:
```
apptainer build spras.sif docker://reedcompbio/spras:v0.1.0
```
to produce the file `spras.sif`. Then, substitute this value as the `container_image` in the submit file.

## Versions:

The versions of this image match the version of the spras package within it.
- v0.1.0: Created an image with SPRAS as an installed python module. This makes SPRAS runnable anywhere with Docker/Singularity. Note that the Snakefile should be
  runnable from any directory within the container.
