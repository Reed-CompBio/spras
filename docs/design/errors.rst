Errors
======

By default, whenever SPRAS runs into a container error (i.e. an internal
algorithm error), the full workflow will fail. However, there are
certain designated errors where we don't want this to be the case (at
the moment, these designated errors are only container timeouts, but
this may be extended to heuristics in the future).

Due to the following design constraints:

- Snakemake does not have support for such errors (the closest being
  ``--keep-going``, which unnecessarily runs failed runs)
- SPRAS occasionally outputs empty files as genuine output
- We need to log errors that happen for user knowledge

we opt to use a ``resource-info.json`` file, which keeps track of the
success/failure status at certain failable parts of the workflow. This
file contains whether or not this part of the workflow succeeded, and if
it failed, how it failed.
