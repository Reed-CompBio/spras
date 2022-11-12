# MinCostFlow Docker image

A Docker image for [MinCostFlow](https://github.com/gitter-lab/min-cost-flow) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/mincostflow).

To create the Docker image run:
```
docker build -t reedcompbio/mincostflow -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
docker run reedcompbio/mincostflow pip list
```
or inspect the Python script arguments:
```
docker run reedcompbio/mincostflow python /MinCostFlow/minCostFlow.py -h
```
Windows users may need to add the prefix `winpty` prefix before these commands.

The Dockerfile intentionally uses the Python image based on Ubuntu instead of an Alpine-based image.
The pip-installable version of the or-tools package [does not support Alpine](https://github.com/google/or-tools/issues/756).

## Testing
Test code is located in `test/MinCostFlow`.
The `input` subdirectory contains different test graphs that each contain 3 test files: `edges.txt`, `sources.txt`, and `targets.txt`.
The expected output graphs for different flow and capacity values are in the `expected` subdirectory.

The Docker wrapper can be tested with `pytest -k test_mcf.py` from the root of the SPRAS repository.

Alternatively, to run the Docker image directly, run the following command from the root of the `spras` repository
``` 
docker run -w /data --mount type=bind,source=/${PWD},target=/data reedcompbio/mincostflow python /MinCostFlow/minCostFlow.py --edges_file /data/test/MinCostFlow/input/graph1/edges.txt --sources_file /data/test/MinCostFlowinput/graph1/sources.txt --targets_file /data/test/MinCostFlowinput/graph1/targets.txt --flow 1 --output graph1 --capacity 1  
```

This will run MinCostFlow on the test input files and write the output files to the root of the `spras` repository.

Windows users may need to escape the absolute paths so that `/data` becomes `//data`, etc.
