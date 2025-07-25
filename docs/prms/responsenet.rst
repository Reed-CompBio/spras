ResponseNet
===========

ResponseNet is a pathway reconstruction algorithm which finds subnetworks using linear programming,
considering an interactome as a way to send 'flow' from sources to targets.
See the `original paper <https://doi.org/10.1038/ng.337>`_ and the corresponding reimplementation of it:
https://github.com/Reed-CompBio/ResponseNet.

ResponseNet takes one optional parameter:

* gamma: (int) controls the size of the output graph: more gamma means more 'flow' gets passed along starting from the sources.
