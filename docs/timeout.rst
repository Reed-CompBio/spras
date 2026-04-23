Timeouts
========

SPRAS allows for per-algorithm timeouts, specified under the global
configuration file. For example, to give the AllPairs algorithm a 1 day
timeout:

.. code:: yaml

   - name: "allpairs"
     include: true
     timeout: 1d

The timeout string parsing is delegated to
`pytimeparse <https://pypi.org/project/pytimeparse/>`__, which allows
for more complicated timeout strings, such as ``3d2h32m``.

**NOTE**: This feature only works with docker at the time of writing.
