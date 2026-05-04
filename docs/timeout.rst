##########
 Timeouts
##########

The SPRAS global configuration can take optional per-algorithm timeouts.
For example, to give the AllPairs algorithm a 1 day timeout:

.. code:: yaml

   - name: "allpairs"
     include: true
     timeout: 1d

The timeout string parsing is delegated to `pytimeparse
<https://pypi.org/project/pytimeparse/>`__ (examples linked here). This
allows for more complicated timeout strings, such as ``3d2h32m``.

If ``timeout`` is not specified, the algorithm will never be interrupted
due to running too long.

**NOTE**: This feature only works with docker and apptainer/singularity
at the time of writing, not dsub.
