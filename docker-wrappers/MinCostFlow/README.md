# MinCostFlow Docker image

A Docker image for [MinCostFlow](https://github.com/gitter-lab/min-cost-flow) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/pathlinker).

To create the Docker image run:
```
docker build -t reedcompbio/mincostflow -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run reedcompbio/mincostflow pip list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/MinCostFlow`.
The `input` subdirectory contains different test graphs that each contain 3 test files: `edges.txt`, `sources.txt` and `targets.txt`.

The Docker wrapper can be tested with `pytest -k test_mcf.py`.

Alternatively, to test the Docker image directly, run the following command from the root of the `spras` repository
``` 
docker run -w /data --mount type=bind,source=/${PWD},target=/data reedcompbio/mincostflow python  minCostFlow.py --edges_file input/graph1/edges.txt --sources_file input/graph1/sources.txt --targets_file input/graph1/targets.txt --flow 1 --output graph1 --capacity 1  
```

This will run PathLinker on the test input files and write the output files to the root of the `spras` repository.

Windows users may need to escape the absolute paths so that `/data` becomes `//data`, etc.

## TODO
- Attribute https://github.com/gitter-lab/min-cost-flow
- Document usage
- MinCostFlow's Dockerfile cannot be converted to Alpine, must use Ubuntu (due to OR-Tools)
