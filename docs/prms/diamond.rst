DIAMOnD
=======

DIAMOnD is a module detection algorithm which finds modules via nodes with *connectivity significance*.

DIAMOnD takes in a few parameters:

* n: int (required), The desired number of DIAMOnD genes to add.
* alpha: int = 1, weight of the seeds. This does nothing if alpha is equal to one. Higher values of alpha prioritize seed nodes during DIAMOnD's several rounds of disease module identification.

External links
++++++++++++++

* Repository: https://github.com/barabasilab/DIAMOnD
* Paper: https://doi.org/10.1371/journal.pcbi.1004120
