MinCostFlow
===========

MinCostFlow is a pathway reconstruction algorithm which and adapts the minimum cost flow
problem to a pathway reconstruction problem, considering the 'flow' between sources and targets, rewarding
flow with sources adding flow and targets removing flow, where each edge
restricts flow while rewarding edges with higher weights.

MinCostFlow takes two optional parameters:

* flow: (int) the amount of flow going through the graph
* capacity: the (float) max capacity for edges

Dataset Usage
-------------

MinCostFlow uses the input's ``sources``, ``targets``, and edge weights. MinCostFlow also
edge direction information.

Implementation Details
----------------------

MinCostFlow's internal implementation only accepts directed interactomes.
SPRAS will automatically convert edges to directed edges as necessary.
For more information, see the section on :ref:`algorithm directionality <directionality>`.

External links
++++++++++++++

* Repository: https://github.com/gitter-lab/min-cost-flow/
* MinCostFlow implementation paper: https://doi.org/10.1038/s41540-020-00167-1
* Idea for MinCostFlow as a PRM: https://doi.org/10.1038/ng.337
