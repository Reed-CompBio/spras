# BowTieBuilder Docker image

A Docker image for [BowTieBuilder](https://github.com/Reed-CompBio/BowTieBuilder-Algorithm) that is available on the [GitHub Container Registry](https://github.com/orgs/Reed-CompBio/packages/container/package/bowtiebuilder).

To create the Docker image run:
```
docker build -t reed-compbio/bowtiebuilder:v1 -f Dockerfile .
```
from this directory.

## Original Paper

The original paper for [BowTieBuilder] can be accessed here:

Supper, J., Spangenberg, L., Planatscher, H. et al. BowTieBuilder: modeling signal transduction pathways. BMC Syst Biol 3, 67 (2009). https://doi.org/10.1186/1752-0509-3-67

## Versions

- `v1`: Initial docker container
- `v2`: Pin BTB file version for reproducible docker builds.
