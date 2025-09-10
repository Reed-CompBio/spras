# docker-wrappers

This folder contains the list of all docker wrappers.

We build these docker images with `buildx` to support multiple docker architectures.

For convenience, we provide a `build.py` python file which pushes a docker image with the architectures
that we want to support.

```
usage: build.py [-h] --dir DIR --version VERSION [--org-name ORG_NAME] [--yes | --no-yes] [--relax | --no-relax] [--push | --no-push]
build.py: error: the following arguments are required: --dir, --version
```

For example, using the default supported `ghcr.io` registry that SPRAS uses, we can build RWR v1:

```
docker login ghcr.io -u reed-compbio
python build.py --dir RWR --version v1
```

You can also push the image using `--push`, which will push the image to the GitHub Container Registry.
