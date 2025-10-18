ResponseNet
===========

ResponseNet is a pathway reconstruction algorithm which finds subnetworks using linear programming,
considering an interactome as a way to send 'flow' from sources to targets.
See the `original paper <https://doi.org/10.1038/ng.337>`_ and the corresponding reimplementation of it:
https://github.com/Reed-CompBio/ResponseNet.

ResponseNet takes one optional parameter:

* gamma: (int) controls the size of the output graph: more gamma means more 'flow' gets passed along starting from the sources.

Dataset Usage
-------------

ResponseNet uses ``sources``, ``targets``, and edge weights. ResponseNet
considers graph directionality.

Implementation Details
----------------------

ResponseNet's internal algorithm only takes in directed graphs.
Any pathway inputted into ResponseNet gets converted into a directed graph,
where undirected edges get converted into two directed edges pointing opposite of one
another.
