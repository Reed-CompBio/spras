RWR
===

RWR, or random walk with restarts, is a source and target independent pathway reconstruction algorithm
that performs PathRank on the input interactome, using the provided prizes.

For a random walk with restarts implementation that uses sources and targets, see STRWR.
RWR takes in two parameters:

* threshold: The number of nodes to have in the final returned subgraph.
* alpha: The damping factor of the internal PathRank algorithm. This is the probability that RWR randomly chooses a neighbor instead of restarting.

RWR is implemented at https://github.com/reed-compbio/rwr.

Dataset Usage
-------------

RWR considers the union of ``sources`` and ``targets`` as the
input active nodes. Input interactome directionality is considered, and the
output subnetwork is also directed.

Implementation Details
----------------------

RWR returns a ranked list of nodes: SPRAS returns the induced subgraph
from the number of nodes corresponding to the user-specified ``threshold``.

Internally, RWR only takes in directed graphs.
SPRAS will automatically convert edges to directed edges as necessary.
For more information, see the section on :ref:`algorithm directionality <directionality>`.
