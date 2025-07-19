MinCostFlow
===========

MinCostFlow is a pathway reconstruction algorithm which and adapts the minimum cost flow
problem to a pathway reconstruction problem, considering the 'flow' between sources and targets, rewarding
flow with sources adding flow and targets removing flow, where each edge
restricts flow while rewarding edges with higher weights.

MinCostFlow takes two optional parameters:

* flow: (int) the amount of flow going through the graph
* capacity: the (float) max capacity for edges
