Omics Integrator 1
==================

Omics Integrator 1 is a pathway reconstruction algorithm. See the source code:
https://github.com/fraenkel-lab/OmicsIntegrator (licensed under BSD-2),
or the associated paper: http://doi.org/10.1371/journal.pcbi.1004879.

OI1 takes some optional arguments:

* noisy_edges: How many times you would like to add noise to the given edge values and re-run the algorithm. 
* shuffled_prizes: How many times the algorithm should shuffle the prizes and re-run
* random_terminals: How many times to apply the given prizes to random nodes in the interactome
* seed: the randomness seed to use
* w: float that affects the number of connected components, with higher values leading to more components
* b: the trade-off between including more prizes and using less reliable edges
* d: controls the maximum path-length from root to terminal nodes
* mu: controls the degree-based negative prizes (default 0.0)
* noise: Standard Deviation of the gaussian noise added to edges in Noisy Edges Randomizations
* g: msgsteiner reinforcement parameter that affects the convergence of the solution and runtime, with larger values leading to faster convergence but suboptimal results (default 0.001)
* r: msgsteiner parameter that adds random noise to edges, which is rarely needed because the ``noisy_edges`` option is recommended instead. (default 0)
* dummy_mode: one of ``terminals``, ``all``, ``others``, or ``file``.

  * ``terminals``: connect the dummy node to all nodes that have been assigned prizes 
  * ``all``: connect the dummy node to all nodes in the interactome (i.e. full set of nodes in graph)
  * ``others``: connect the dummy node to all nodes that are not terminal nodes (i.e. nodes without prizes)
  * ``file``: connect the dummy node to a specific list of nodes provided in a file

Dataset Usage
-------------

OmicsIntegrator1 prefers ``prize``s, but will take the union of ``sources`` and ``targets``
and set their 'prize' to 1 if ``prize`` is not specified. If any ``dummy_nodes`` are specified,
these are passed to OmicsIntegrator1 and can have their behavior configured with ``dummy_mode``.

OmicsIntegrator1 accepts mixed directionality graphs.
