ST_RWR
==========

ST_RWR, or random walk with restarts, is a source and target dependent pathway reconstruction algorithm
that performs PathRank on the input interactome, using its edge weights, prizes, sources, and targets.

For a random walk with restarts implementation that does not use  sources and targets, see RWR.

* threshold: The number of nodes to have in the final returned subgraph.
* alpha: The damping factor of the internal PathRank algorithm. This is the probability that RWR randomly chooses a neighbor instead of restarting.

ST_RWR is implemented at https://github.com/reed-compbio/rwr.
