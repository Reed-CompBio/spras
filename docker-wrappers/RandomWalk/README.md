# RandomWalk Algorithm

This is a simple algorithm that generates a random walk with restart in a 2D plane. The algorithm will generate the possibility of each node to be visited if we start from a random node and walk to a random direction with a restart probability and a teleport probability. This possibility indicates the importance of the node in the graph. The higher the possibility, the more important the node is.

## How to use

```

$ python random_walk.py -h

usage: random_walk.py [-h] --edges_file EDGES_FILE --sources_file

                      SOURCES_FILE --targets_file TARGETS_FILE --output_nodes

                      OUTPUT_NODES --output_edges OUTPUT_EDGES


Random Walk path reconstruction


optional arguments:

  -h, --help            show this help message and exit

  --edges_file EDGES_FILE

                        Path to the edges file

  --sources_file SOURCES_FILE

                        Path to the source node file

  --targets_file TARGETS_FILE

                        Path to the target node file

  --output_nodes OUTPUT_NODES

                        Path to the output file for nodes

  --output_edges OUTPUT_EDGES

                        Path to the output file for edges

```

## Example behavior

edge file:

```

Node1 Node2 Weight

A D 1

B D 1

C D 1

D E 1

D F 1

D G 1

```

source_nodes file:

```

node prize

A 1

B 1

C 1

```

target_nodes file:

```

node prize

E 1

F 1

G 1

```

output_nodes file:

```

node pr r_pr final_pr

G 0.09361880756187185 0.12957574978407632 0.09361880756187185

A 0.12957574978407632 0.09361880756187185 0.09361880756187185

B 0.12957574978407632 0.09361880756187185 0.09361880756187185

D 0.3304163279621552 0.3304163279621552 0.3304163279621552

F 0.09361880756187185 0.12957574978407632 0.09361880756187185

C 0.12957574978407632 0.09361880756187185 0.09361880756187185

E 0.09361880756187185 0.12957574978407632 0.09361880756187185

```

output_edges file:

```

Node1 Node2 Weight

A D 0.09361880756187185

B D 0.09361880756187185

D E 0.11013877598738507

D F 0.11013877598738507

D G 0.11013877598738507

C D 0.09361880756187185

```
