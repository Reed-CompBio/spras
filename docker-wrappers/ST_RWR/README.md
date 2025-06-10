## Notes
The random walk with restarts algorithm requires a directed input network. However, the algorithm in its current form will accept an undirected input network and interpret it as a directed network. The resulting output from an undirected network does not accuratly represent directionality.

## Building docker fileAdd commentMore actions
to build a new docker image for rwr navigate to the /docker-wrappers/rwr directory and enter:
```
docker build -t ade0brien/strwr -f Dockerfile .
```

## Testing
Test code is located in `test/ST_RWR`.
The `input` subdirectory contains test files `strwr-network.txt`, `strwr-sources.txt`, and `strwr-targets.txt`
The Docker wrapper can be tested with `pytest`.