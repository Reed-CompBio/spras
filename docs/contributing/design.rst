###############
 SPRAS Designs
###############

SPRAS makes a few high-level design decisions. We motivate them here.

..
   Right now, this only talks about immutable outputs. In the future, this may include, and is not limited to:

..
   container-agonistic volumes, directionality, parameter tuning, and typed configs/algorithms.

*******************
 Immutable Outputs
*******************

During benchmarking runs, SPRAS data is uploaded to the `Open Science
Data Federation <https://osg-htc.org/services/osdf>`__. OSDF enforces an
immutable file structure, where files can never be deleted or rewritten.
By default, SPRAS does not have immutable files. However, in SPRAS
configurations, the ``immutable_files`` parameter can be enabled to make
files fully immutable where no file with the same file name will be
written with different data.

To do this, SPRAS tags all datasets, gold standards, and algorithms with
a version hash, which is effectively the current version of how SPRAS
processes that data in-code.

In implementation, this version hash is the hash of the `RECORD
<https://packaging.python.org/en/latest/specifications/recording-installed-packages/#the-record-file>`__
file, which contains hashes of all 'installed' files. When SPRAS is not
installed in development mode (i.e. without the ``--editable`` flag),
the ``RECORD`` file hashes all Python source files, leading to the
desired effect that the version hash changes when the source code
changes. In development mode, the ``RECORD`` file does not change when
source code is changed.
