Omics Integrator 2
===================

Omics Integrator 2 is a pathway reconstruction algorithm. See the source code:
https://github.com/fraenkel-lab/OmicsIntegrator2 (licensed under BSD-3).

OI2 takes a few optional arguments:

* output_file: the name of the output file, which will overwrite any existing file with this name
* w: (Omega) the weight of the edges connecting the dummy node to the nodes selected by dummyMode (default: 6)
* b: (Beta) scaling factor of prizes (default: 1)
* g: (Gamma) multiplicative edge penalty from degree of endpoints (default: 20)
* noise: Standard Deviation of the gaussian noise added to edges in Noisy Edges Randomizations.
* noisy_edges: An integer specifying how many times to add noise to the given edge values and re-run.
* random_terminals: An integer specifying how many times to apply your given prizes to random nodes in the interactome and re-run
* dummy_mode: Tells the program which nodes in the interactome to connect the dummy node to. (default: terminals)
    * "terminals" = connect to all terminals
    * "others" = connect to all nodes except for terminals
    * "all" = connect to all nodes in the interactome.
* seed: The random seed to use for this run.


Dataset Usage
-------------

OmicsIntegrator2 prefers ``prize``s, but will take the union of ``sources`` and ``targets``
and set their 'prize' to 1 if ``prize`` is not specified.

OmicsIntegrator2 does not consider graph directionality.
