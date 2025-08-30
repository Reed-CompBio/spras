# DOMINO Docker image

A Docker image for [DOMINO](https://github.com/Shamir-Lab/DOMINO) that is available on the [GitHub Container Registry](https://github.com/orgs/Reed-CompBio/packages/container/package/domino).

DOMINO outputs multiple active modules, which SPRAS combines into a single pathway.
It is [non-deterministic](https://github.com/Shamir-Lab/DOMINO/issues/5) and cannot be made deterministic with a seed.

To create the Docker image run:
```
docker build -t reed-compbio/domino -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run reed-compbio/domino pip list
```
The `winpty` prefix is only needed on Windows.

## TODO
- Resolve upstream ValueError with small inputs https://github.com/Shamir-Lab/DOMINO/issues/11
- Use cache or reuse slices files from previous runs on the same network
