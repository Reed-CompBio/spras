# All Pairs Shortest Paths Docker image

A Docker image for All Pairs Shortest Paths that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/allpairsshortestpath).

To create the Docker image run:
```
docker build -t reedcompbio/allpairsshortestpath -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
docker run reedcompbio/allpairsshortestpath pip list
```
Windows users may need to add the prefix `winpty` prefix before these commands.


## Testing
Test code is located in `test/AllPairs`.
The `input` subdirectory contains a sample network and source/target file, along with a network and source/target file to check for the correctness of All Pairs Shortest Path.
The expected output graphs for the sample network is in the `expected` subdirectory.

The Docker wrapper can be tested with `pytest -k test_ap.py` from the root of the SPRAS repository.


## Notes
- The all-pairs-shortest-paths code is located locally in SPRAS (since the code is short). It is under docker-wrappers/Allpairs
- samples of an input network and source/target file are located under test/AllPairs/input
