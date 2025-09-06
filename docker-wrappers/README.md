# docker-wrappers

This folder contains the list of all docker wrappers.

We build these docker images with `buildx` to support multiple docker architectures.

For convenience, we provide a `push.py` python file which pushes a docker image with the architectures
that we want to support.

```
usage: push.py [-h] --dir DIR --version VERSION [--org-name ORG_NAME] [--yes | --no-yes] [--relax | --no-relax] [--nopush | --no-nopush]
push.py: error: the following arguments are required: --dir, --version
```

For example, using the default supported `ghcr.io` registry that SPRAS uses, we can push RWR v1:

```
docker login ghcr.io -u reed-compbio
python push.py --dir RWR --version v1
```

You can also build the image without pushing it using `--nopush`, which will load the image into docker.
