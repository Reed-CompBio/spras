PathLinker
==========

PathLinker is a pathway reconstruction algorithm which links the sources and target
of the input interactome with a k-shortest paths (implemented with Yen's algorithm)
to a pathway reconstruction context.


PathLinker takes one optional argument:

* k: The number of paths to find (*k* shortest paths).

Dataset Usage
-------------

PathLinker uses ``sources``, ``targets``, and edge weights. PathLinker
considers graph directionality.

Implementation Details
----------------------

PathLinker's internal algorithm only takes in directed graphs.
Any pathway inputted into PathLinker gets converted into a directed graph,
where undirected edges get converted into two directed edges pointing opposite of one
another.


External links
++++++++++++++

* Source code: https://github.com/Murali-group/PathLinker
* Associated papers: https://doi.org/10.1038/npjsba.2016.2 and https://doi.org/10.1089/cmb.2012.0274.
