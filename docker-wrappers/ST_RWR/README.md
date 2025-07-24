# Source-Targets Random Walk with Restarts

A Docker image for [ST-RWR](https://github.com/Reed-CompBio/rwr) that is available on [DockerHub](https://hub.docker.com/repository/docker/reedcompbio/st_rwr).

## Notes
The random walk with restarts algorithm requires a directed input network. However, the algorithm in its current form will accept an undirected input network and interpret it as a directed network. The resulting output from an undirected network does not accuratly represent directionality.

## Building Docker File
To build a new docker image for ST_RWR navigate to the /docker-wrappers/ST_RWR directory and enter:

```
docker build -t reedcompbio/str-wr -f Dockerfile .
```

## Testing
Test code is located in `test/ST_RWR`.
The `input` subdirectory contains test files `strwr-network.txt`, `strwr-sources.txt`, and `strwr-targets.txt`
The Docker wrapper can be tested with `pytest`.