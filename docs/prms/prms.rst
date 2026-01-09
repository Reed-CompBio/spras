Pathway Reconstruction Methods
=====================================

.. note::
   While every algorithm here is broadly labelled as a pathway reconstruction method,
   there are other sub-types of algorithms that have more specialized capabilities than the rest.
   Currently, SPRAS also supports edge orientation algorithms (e.g. MEO) and active module identifiers/disease module mining methods (e.g. DOMINO).

This is the list of SPRAS's supported pathway reconstruction methods. Each subpage comes with a description of the algorithm,
its source code and associated paper (if one exists), and its 'dataset usage,' or parts of a dataset that it will utilize when
running pathway reconstruction. Implementation details are also provided, for users wondering about any
important decisions that differentiate the SPRAS-wrapped version from the original
algorithm.

.. _directionality:

Directionality Details
----------------------

Some algorithms only accept fully undirected or fully directed interactomes as input. For input
data, SPRAS will try to preserve as much directionality information as possible. Mixed interactomes
are also accepted in SPRAS.

SPRAS will automatically convert the input interactome to the desired directionality by the algorithm:
this can mean that, for some algorithms, interactome direction may be ignored. Other algorithms will
consider interactome directionality, whether by accepting mixed interactomes directly,
or converting undirected edges into directed edges.

For converting undirected edges to directed edges, unless otherwise specified, undirected edges
will be converted into two directed edges pointing opposite of one another.

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
