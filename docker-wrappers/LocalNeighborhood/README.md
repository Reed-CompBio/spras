# Local Neighborhood Docker image

A simple pathway reconstruction algorithm used to welcome new contributors.
The algorithm takes a network and a list of nodes as input.
It outputs all edges in the network that have a node from the list as an endpoint.

New contributors complete the `Dockerfile` to wrap the implementation in `local_neighborhood.py`.

## Usage
```
$ python local_neighborhood.py -h
usage: local_neighborhood.py [-h] --network NETWORK --nodes NODES --output OUTPUT  

Local neighborhood pathway reconstruction

optional arguments:
  -h, --help         show this help message and exit
  --network NETWORK  Path to the network file with '|' delimited node pairs
  --nodes NODES      Path to the nodes file
  --output OUTPUT    Path to the output file that will be written
```

## Example behavior
Network file:
```
A|B
C|B
C|D
D|E
A|E
```

Nodes file:
```
A
B
```

Output file:
```
A|B
C|B
A|E
```