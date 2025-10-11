DOMINO
======

DOMINO is an active module identification algorithm (which is broadly categorized in SPRAS under 'disease mining algorithms'). See the associated paper: https://doi.org/10.15252/msb.20209593
and the associated MIT-licensed codebase: https://github.com/Shamir-Lab/DOMINO/.

DOMINO has two optional parameters:

* slice_threshold: the p-value threshold for considering a slice as relevant
* module_threshold: the p-value threshold for considering a putative module as final module

Dataset Usage
-------------

DOMINO requires the `active` column to be set. DOMINO does not consider edge weights,
but DOMINO does consider graph directionality.

Implementation Details
----------------------

If the input dataframe is empty or too 'small' (where no modules are found),
SPRAS will instead emit an empty output file.
