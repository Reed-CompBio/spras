##########
 Timeouts
##########

The SPRAS global configuration can take optional per-algorithm timeouts.
For example, to give a specific run of the PathLinker algorithm a 1 day
timeout:

.. code:: yaml

   - name: "pathlinker"
     include: true
     runs:
       run1:
         timeout: 1d
         k: 200

The timeout string parsing is delegated to `pytimeparse
<https://pypi.org/project/pytimeparse/>`__ (examples linked here). This
allows for more complicated timeout strings, such as ``3d2h32m``.

If ``timeout`` is not specified, the algorithm will never be interrupted
due to running too long.

**NOTE**: This feature only works with docker and apptainer/singularity
at the time of writing, not dsub.

*********************
 Configuration notes
*********************

Since ``timeout`` is a run parameter, it can also be moved to the top
level of an algorithm configuration, where that value will become the
default unless otherwise specified in a specific run.

.. code:: yaml

   - name: "pathlinker"
     include: true
     timeout: 1d
     runs:
       run1:
         # this uses timeout: 2d
         timeout: 2d
         k: 200
       run2:
         # this uses timeout: 1d
         k: 100

This is also useful for algorithms which take in no parameters, such as
``allpairs``:

.. code:: yaml

   - name: "allpairs"
     include: true
     timeout: 1d
