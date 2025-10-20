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

BowTieBuilder uses ``sources``, ``targets``, and edge weights. Input graph
directionality is considered.

Implementation Details
----------------------

BowTieBuilder's internal algorithm only takes in directed graphs.
Any pathway inputted into BowTieBuilder gets converted into a directed graph,
where undirected edges get converted into two directed edges pointing opposite of one
another.
