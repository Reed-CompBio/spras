# All Pairs Shortest Paths Docker image

A Docker image for All Pairs Shortest Paths that is available on the [GitHub Container Registry](https://github.com/orgs/Reed-CompBio/packages/container/package/allpairs).
This [algorithm](https://github.com/Reed-CompBio/all-pairs-shortest-paths) was implemented by the SPRAS team and relies on the NetworkX [`shortest_path`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.generic.shortest_path.html) function.

To create the Docker image run:
```
docker build -t reed-compbio/allpairs -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
docker run reed-compbio/allpairs pip list
```


## Testing
Test code is located in `test/AllPairs`.
The `input` subdirectory contains a sample network and source/target file, along with a network and source/target file to check for the correctness of All Pairs Shortest Path.
The expected output graphs for the sample networks are in the `expected` subdirectory.

The Docker wrapper can be tested with `pytest -k test_ap.py` from the root of the SPRAS repository.


## Notes
- Samples of an input network and source/target file are located under test/AllPairs/input.

## Versions:
- (docker hub) v1: Initial version. Copies source file from SPRAS repository.
- v1: Add bash, which is not available in Alpine Linux.
