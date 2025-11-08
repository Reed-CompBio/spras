ST_RWR
======

ST_RWR, or source-target random walk with restarts, is a source and target dependent pathway reconstruction algorithm
that performs PathRank on the input interactome, using its edge weights, prizes, sources, and targets.

For a random walk with restarts implementation that does not use  sources and targets, see RWR.

* threshold: The number of nodes to have in the final returned subgraph.
* alpha: The damping factor of the internal PathRank algorithm. This is the probability that RWR randomly chooses a neighbor instead of restarting.

ST_RWR is implemented at https://github.com/reed-compbio/rwr.

Dataset Usage
-------------

ST_RWR considers ``sources`` and ``targets``. ST_RWR considers interactome directionality,
and the output subnetwork is also directed.

Implementation Details
----------------------

ST_RWR returns a ranked list of nodes: SPRAS returns the induced subgraph
from the number of nodes corresponding to the user-specified ``threshold``.

Internally, ST_RWR only takes in directed graphs.
SPRAS will automatically convert edges to directed edges as necessary.
For more information, see the section on :ref:`algorithm directionality <directionality>`.
