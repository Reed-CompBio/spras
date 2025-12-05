BowTieBuilder
=============

BowTieBuilder is a pathway reconstruction algorithm which constructs pathways in a 'bowtie'-like
fashion, finding the intersections of shortest paths between sources and targets and using those nodes as a basis
for generating a new reconstructed network.

BowTieBuilder does not take in any arguments.

* Repository: https://github.com/Reed-CompBio/BowTieBuilder-Algorithm
* Paper: https://doi.org/10.1186/1752-0509-3-67

Dataset Usage
-------------

BowTieBuilder uses ``sources``, ``targets``, edge weights, and edge direction information.

Implementation Details
----------------------

BowTieBuilder's internal implementation only takes in directed interactomes.
SPRAS will automatically convert edges to directed edges as necessary.
For more information, see the section on :ref:`algorithm directionality <directionality>`.
