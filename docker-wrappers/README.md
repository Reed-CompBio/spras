# docker-wrappers

This folder contains the list of all docker wrappers.

We build these docker images with `buildx` to support multiple docker architectures.

## `build.py`

For convenience, we provide a `build.py` python file which pushes a docker image with the architectures
that we want to support.

```
usage: build.py [-h] --dir DIR --version VERSION [--org-name ORG_NAME] [--yes | --no-yes] [--relax | --no-relax] [--push | --no-push] [--load | --no-load]
build.py: error: the following arguments are required: --dir, --version
```

For example, using the default supported `ghcr.io` registry that SPRAS uses, we can build RWR v1:

```sh
docker login ghcr.io -u reed-compbio
python build.py --dir RWR --version v1
```

> [!NOTE]
> To use a docker image locally with this script, you must use `--load`. See below for more information.

There are also two boolean settings:
- `--push`: pushes the image to the GitHub Container Registry.
- `--load`: loads the image into your local container registry. This only works with your system architecture, and multi-architecture builds can be tested by omitting `--load`.

In general, use `--push` for production, `--load` for local development, and omit both to test the docker container on all architectures (which will happen on CI.)
