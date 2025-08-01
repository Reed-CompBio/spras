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
* g: (Gamma) multiplicative edge penalty from degree of endpoints
* r: msgsteiner parameter that adds random noise to edges, which is rarely needed. (default 0)
