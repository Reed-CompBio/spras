SPRAS Designs
=============

SPRAS makes a few high-level design decisions. We motivate them here.

.. Right now, this only talks about immutable outputs. In the future, this may include, and is not limited to:
.. container-agonistic volumes, directionality, parameter tuning, and typed configs/algorithms.

Immutable Outputs
-----------------

During benchmarking runs, SPRAS data is uploaded to the `Open Science
Data Federation <https://osg-htc.org/services/osdf>`__, which uses an
immutable file structure, where files can never be deleted or rewritten.
By default, SPRAS does not have immutable files. However, in SPRAS
configurations, the ``osdf_immutable`` parameter can be enabled to make
files fully immutable where no file with the same file name will be
written with different data.

To do this, SPRAS tags all datasets, gold standards, and algorithms with
a version hash, which is effectively the current version of how SPRAS
processes that data in-code.
