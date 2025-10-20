All Pairs
=========

All Pairs Shortest Paths is an algorithm which, given a weighted interactome,
will return the induced edge subnetwork of the interactome consisting
of all of the shortest paths from every single source to every single target
with respect to a cartesian product.

All Pairs does not take any arguments. Its source code is at https://github.com/Reed-CompBio/all-pairs-shortest-paths
licensed under MIT.

Dataset Usage
-------------

All Pairs Shortest Paths uses ``sources``, ``targets``, and edge weights.
All Pairs Shortest Paths also can incorporate graph directionality: it accepts directed, undirected, and mixed graphs.
However, All Pairs Shortest Paths always returns an undirected subnetwork.

Implementation Details
----------------------

When All Pairs Shortest Paths gets passed a mixed graph, it considers the entire graph to be
directed, by converting all undirected edges to two directed edges pointing
opposite of one another.
