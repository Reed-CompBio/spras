Pathway Reconstruction Methods
=====================================

.. note::
   While every algorithm here is broadly labelled as a pathway reconstruction method,
   there are other sub-types of algorithms that have more specialized capabilities than the rest.
   Currently, SPRAS also supports edge orientation algorithms (e.g. MEO) and active module identifiers/disease module mining methods (e.g. DOMINO).

This is the list of SPRAS's supported pathway reconstruction methods. Each subpage comes with a description of the algorithm,
its source code and associated paper (if one exists), and its 'dataset usage,' or parts of a dataset that it will utilize when
running pathway reconstruction. Implementation details are also provided, for users wondering about any
important decisions that differentriate the SPRAS-wrapped version from the actual
algorithm.

.. toctree::
   :maxdepth: 1
   :caption: All Pairs

   allpairs

.. toctree::
   :maxdepth: 1
   :caption: BowTieBuilder

   bowtiebuilder

.. toctree::
   :maxdepth: 1
   :caption: DOMINO

   domino

.. toctree::
   :maxdepth: 1
   :caption: MEO

   meo

.. toctree::
   :maxdepth: 1
   :caption: MinCostFlow

   mincostflow

.. toctree::
   :maxdepth: 1
   :caption: Omics Integrator I

   oi1

.. toctree::
   :maxdepth: 1
   :caption: Omics Integrator II

   oi2

.. toctree::
   :maxdepth: 1
   :caption: PathLinker

   pathlinker

.. toctree::
   :maxdepth: 1
   :caption: ResponseNet

   responsenet

.. toctree::
   :maxdepth: 1
   :caption: RWR

   rwr

.. toctree::
   :maxdepth: 1
   :caption: STRWR

   strwr
