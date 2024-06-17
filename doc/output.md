## File format
### Universal Output File
Output files include a header row and rows providing attributes for each node.
The header row is `Node1    Node2   Rank    Direction` for every output file.
Each row lists the two nodes that are connected with an edge, the rank for that edge, and a directionality column to indicate whether the edge is directed or undirected.
The directionality values are either a 'U' for an undirected edge or a 'D' for a directed edge.

For example:
```
Node1	Node2	Rank	Direction
A       B	    1	    D
B	    C	    1	    D
B	    D	    1	    U
D	    A	    1	    U
```
