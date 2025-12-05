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
uses edge direction information, but returns an undirected subnetwork.

Implementation Details
----------------------

Internally, ResponseNet only takes in directed graphs.
SPRAS will automatically convert edges to directed edges as necessary.
For more information, see the section on :ref:`algorithm directionality <directionality>`.
