ResponseNet
===========

ResponseNet is a pathway reconstruction algorithm which finds subnetworks using integer linear programming,
considering an interactome as a way to send 'flow' from sources to targets.
See the `original paper <https://doi.org/10.1038/ng.337>`_ and the corresponding reimplementation of it:
https://github.com/Reed-CompBio/ResponseNet.

ResponseNet takes one optional parameter:

* gamma: (int) the size of the output graph: more gamma means more 'flow' needs to be passed through the sources.
