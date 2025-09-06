# Source-Targets Random Walk with Restarts

A Docker image for [RWR](https://github.com/Reed-CompBio/rwr) that is available on the [GitHub Container Registry](https://github.com/orgs/Reed-CompBio/packages/container/package/rwr).

## Notes
The random walk with restarts algorithm requires a directed input network. However, the algorithm in its current form will accept an undirected input network and interpret it as a directed network. The resulting output from an undirected network does not accurately represent directionality.

## Building docker file
To build a new docker image for RWR navigate to the /docker-wrappers/rwr directory and enter:

```
docker build -t reed-compbio/rwr -f Dockerfile .
```

## Testing
Test code is located in `test/RWR`.
The `input` subdirectory contains test files `rwr-network.txt`, `rwr-sources.txt`, and `rwr-targets.txt`
The Docker wrapper can be tested with `pytest`.
