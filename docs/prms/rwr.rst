RWR
==========

RWR, or random walk with restarts, is a source and target independent pathway reconstruction algorithm
that performs PathRank on the input interactome, using the provided prizes.

For a random walk with restarts implementation that uses sources and targets, see STRWR.
RWR takes in two parameters:

* threshold: The number of nodes to have in the final returned subgraph.
* alpha: The damping factor of the internal PathRank algorithm. This is the probability that RWR randomly chooses a neighbor instead of restarting.
