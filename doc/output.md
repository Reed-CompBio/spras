## File formats

### Pathway output format
Output pathway files in the standard SPRAS format include a header row and rows providing attributes for each edge.
The header row is `Node1    Node2   Rank    Direction`.
Each row lists the two nodes that are connected with an edge, the rank for that edge, and a directionality column to indicate whether the edge is directed or undirected.
The directionality values are either a 'U' for an undirected edge or a 'D' for a directed edge, where the direction is from Node1 to Node2.
Pathways that do not contain ranked edges can output all 1s in the Rank column.

For example:
```
Node1	Node2	Rank	Direction
A	B	1	D
B	C	1	D
B	D	2	U
D	A	3	U
```
