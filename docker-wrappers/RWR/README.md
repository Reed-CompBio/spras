# RWR Docker image

A Docker image for the random-walk-with-start algorithm that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/random-walk-with-restart).

To create the Docker image run:
```
docker build -t reedcompbio/random-walk-with-restart -f Dockerfile .
```
from this directory.

To inspect the installed Python packages:
```
winpty docker run reedcompbio/random-walk-with-restart pip list
```
The `winpty` prefix is only needed on Windows.

## Testing
Test code is located in `test/RWR`.
The `input` subdirectory contains test files `source_nodes.txt`, `target_nodes.txt` and `edges.txt`.
The Docker wrapper can be tested with `pytest` or a unit test with `pytest -k test_rwr.py`.

Alternatively, to test the Docker image directly, run the following command from the root of the `spras` repository
```
docker run -w /data --mount type=bind,source=/${PWD},target=/data reedcompbio/random-walk-with-restart python random_walk.py \
  /data/test/RWR/input/edges.txt /data/test/RWR/input/source_nodes.txt /data/test/RWR/input/target_nodes.txt --damping_factor 0.85 --selection_function min --threshold 0.001 --w 0.0001 --output_file /data/test/RWR/output/output.txt
```
This will run RWR on the test input files and write the output files to the root of the `spras` repository.
Windows users may need to escape the absolute paths so that `/data` becomes `//data`, etc.

