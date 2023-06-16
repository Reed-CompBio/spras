# RWwR Docker image

A Docker image for the random-walk-with-start algorithm that is available on [DockerHub](https://hub.docker.com/repository/docker/erikliu24/rwwr).

To create the Docker image run:
```
docker build -t eriliu24/RandomWalk -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run erikliu24/rwwr pip list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/RandomWalk`.
The `input` subdirectory contains test files `source_nodes.txt`, `target_nodes.txt` and `edges.txt`.
The Docker wrapper can be tested with `pytest`.

Alternatively, to test the Docker image directly, run the following command from the root of the `spras` repository
```
docker run -w /data --mount type=bind,source=/${PWD},target=/data erikliu24/rwwr python random_walk.py \
  /data/test/RandomWalk/input/edges.txt /data/test/RandomWalk/input/source_nodes.txt /data/test/RandomWalk/input/target_nodes.txt --damping_factor 0.85 --selection_function min --threshold 0.001 --output_file /data/test/RandomWalk/output/output.txt
```
This will run RWR on the test input files and write the output files to the root of the `spras` repository.
Windows users may need to escape the absolute paths so that `/data` becomes `//data`, etc.

