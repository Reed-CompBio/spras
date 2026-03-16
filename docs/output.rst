File formats
============

All SPRAS file formats are tab-separated values.

Node file
---------

Node files include a header row and rows providing attributes for each
node. One column is for the node identifier and must have the header
value ``NODEID``. All other columns specify additional node attributes
such as prizes. Any nodes that are listed in a node file but are not
present in one or more edges in the edge file will be removed. For
example:

+--------+-------+---------+---------+--------+-------+
| NODEID | prize | sources | targets | active | dummy |
+========+=======+=========+=========+========+=======+
| A      | 1.0   |         | True    | True   | True  |
+--------+-------+---------+---------+--------+-------+
| B      | 3.3   | True    |         | True   |       |
+--------+-------+---------+---------+--------+-------+
| C      | 2.5   |         | True    | True   |       |
+--------+-------+---------+---------+--------+-------+
| D      | 1.9   | True    | True    | True   |       |
+--------+-------+---------+---------+--------+-------+

A secondary format provides only a list of node identifiers and uses the
filename as the node attribute, as in the example ``sources.txt``. This
format may be deprecated.

Edge file
---------

Edge files do not include a header row. Each row lists the two nodes
that are connected with an edge, the weight for that edge, and,
optionally, a directionality column to indicate whether the edge is
directed or undirected. The directionality values are either a 'U' for
an undirected edge or a 'D' for a directed edge. If the directionality
column is not included, SPRAS will assume that the file's edges are
entirely undirected. The weights are typically in the range [0,1] with 1
being the highest confidence for the edge.

For example:

+---+---+------+---+
| A | B | 0.98 | U |
+===+===+======+===+
| B | C | 0.77 | D |
+---+---+------+---+

or

+---+---+------+
| A | B | 0.98 |
+===+===+======+
| B | C | 0.77 |
+---+---+------+

Gold Standard
-------------

Nodes
~~~~~

Gold standard node files are txt files and do not include a header row.

Each row in the file represents a single node identifier. The file is
structured as a single column with one node per line. These nodes
typically correspond to gene or protein identifiers that are relevant to
the biological pathway of interest.

For example:

::

   A
   B
   C

Pathway output format
---------------------

Output pathway files in the standard SPRAS format include a header row
and rows providing attributes for each edge. The header row is
``Node1    Node2   Rank    Direction``. Each row lists the two nodes
that are connected with an edge, the rank for that edge, and a
directionality column to indicate whether the edge is directed or
undirected. The directionality values are either a 'U' for an undirected
edge or a 'D' for a directed edge, where the direction is from Node1 to
Node2. Pathways that do not contain ranked edges can output all 1s in
the Rank column.

For example:

+-------+-------+------+------------+
| Node1 | Node2 | Rank | Direction  |
+=======+=======+======+============+
| A     | B     | 1    | D          |
+-------+-------+------+------------+
| B     | C     | 1    | D          |
+-------+-------+------+------------+
| B     | D     | 2    | U          |
+-------+-------+------+------------+
| D     | A     | 3    | U          |
+-------+-------+------+------------+
