<!-- Generate README to describe the RandomWalk Algorithm -->

# Random Walk with Restart (RWwR) Algorithm
The algorithm generates a random walk, considering the probability of each node being visited based on its importance in the graph. The RWwR algorithm incorporates a restart probability and a teleport probability, which affect the traversal behavior. This algorithm will calculate the edge flux of each edge in the graph based on the results from RWwR algorithm as well to represent the importance of each edge in the graph.

## Background
The RWwR algorithm draws inspiration from the TieDIE algorithm developed by Evan O. Paull and others. The TieDIE algorithm aims to discover causal pathways that link genomic events to transcriptional states using a method called Tied Diffusion Through Interacting Events. You can find more information about the TieDIE algorithm in the research paper titled "Discovering causal pathways linking genomic events to transcriptional states using Tied Diffusion Through Interacting Events (TieDIE)" published in the Bioinformatics journal, Volume 29, Issue 21, November 2013.

The RWwR algorithm modifies the TieDIE algorithm to generate random walks in a 2D plane while considering the importance of each node. The main idea for RWwR is to firstly run pagerank algorithm on the graph based on the given source set, edge weights, and node prizes. Then, the RWwR will perform a pagerank algorithm on the reversed graph starting from the target set. The RWwR algorithm will then combine the two pagerank results to generate a final result. With the calculation of the edge flux based on the final result for each node, we are able to identify the importance of each node and each edge in the graph.
## How to use

```
$ python random_walk.py -h
usage: random_walk.py [-h] --edges_file EDGES_FILE --sources_file
                      SOURCES_FILE --targets_file TARGETS_FILE
                      [--damping_factor DAMPING_FACTOR]
                      [--selection_function SELECTION_FUNCTION]
                      --output_file OUTPUT_FILE

Random-walk-with-restart path reconstruction

optional arguments:
  -h, --help            show this help message and exit
  --edges_file EDGES_FILE
                        Path to the edges file
  --sources_file SOURCES_FILE
                        Path to the source node file
  --targets_file TARGETS_FILE
                        Path to the target node file
  --damping_factor DAMPING_FACTOR
                        Select a damping factor between 0 and 1 for the random walk with restart (default: 0.85)
  --selection_function SELECTION_FUNCTION
                        Select a function to use (min for minimum/sum for sum/avg for average/max for maximum)
  --output_file OUTPUT_FILE
                        Path to the output files
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

output_file file:
```
Node1 Node2 Weight Placeholder
A D 0.12957574978407632 
D E 0.11013877598738507 
D F 0.11013877598738507 
D G 0.11013877598738507 
B D 0.12957574978407632 
C D 0.12957574978407632 
F 0.09361880756187185 0.12957574978407632 0.09361880756187185
A 0.12957574978407632 0.09361880756187185 0.09361880756187185
D 0.3304163279621552 0.3304163279621552 0.3304163279621552
E 0.09361880756187185 0.12957574978407632 0.09361880756187185
G 0.09361880756187185 0.12957574978407632 0.09361880756187185
B 0.12957574978407632 0.09361880756187185 0.09361880756187185
C 0.12957574978407632 0.09361880756187185 0.09361880756187185
```

## References
- Evan O. Paull and others, Discovering causal pathways linking genomic events to transcriptional states using Tied Diffusion Through Interacting Events (TieDIE), *Bioinformatics*, Volume 29, Issue 21, November 2013, Pages 2757–2764, [doi.org/10.1093/bioinformatics/btt471](https://academic.oup.com/bioinformatics/article/29/21/2757/195824)