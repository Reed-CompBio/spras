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
uses edge direction information.

Implementation Details
----------------------

Internally, PathLinker only takes in directed graphs.
SPRAS will automatically convert edges to directed edges as necessary.
For more information, see the section on :ref:`algorithm directionality <directionality>`.


External links
++++++++++++++

* Source code: https://github.com/Murali-group/PathLinker
* Associated papers: https://doi.org/10.1038/npjsba.2016.2 and https://doi.org/10.1089/cmb.2012.0274.
