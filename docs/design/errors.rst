########
 Errors
########

By default, whenever SPRAS runs into a container error (i.e. an internal
algorithm error), the full workflow will fail. However, there are
certain designated errors where we don't want this to be the case.

Due to the following design constraints:

-  Snakemake does not have support for such errors (the closest being
   ``--keep-going``, which unnecessarily runs failed runs)
-  SPRAS occasionally outputs empty files as genuine output
-  We need to log errors that happen for user knowledge

we opt to use an ``artifact-info.json`` file, which keeps track of the
success/failure status at certain failable parts of the workflow. This
file contains whether or not this part of the workflow succeeded, and if
it failed, how it failed.

The ``artifact-info.json`` stores a JSON object, containing:

-  The key ``status``, which is either the value ``success`` or
   ``error``, depending on what happened in the workflow.

-  If ``status`` is ``error``, we store associated error details in the
   ``details`` key, which contains an object:

   -  The ``details`` object varies per error in the form of a tagged
      union: they are differentiated by the ``type`` key. We describe
      each error down below.

*************
 Error Types
*************

With the above schema, we detail the ``details`` key below.

Timeout
=======

Timeout has ``type: timeout``, with a single key ``duration``, which
describes the ``timeout`` value associated to that run.
