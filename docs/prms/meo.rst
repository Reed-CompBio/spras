MEO
===

MEO, or Maximum Edge Orientation, is a pathway orientation algorithm, which takes in a mixed directionality interactome
and returns a fully directed interactome. See the associated paper: https://doi.org/10.1093/nar/gkq1207,
or the BSD-3-licensed codebase: https://github.com/agitter/meo/.

MEO takes in three optional parameters:

* max_path_length: The maximal path (from any source to any target) lengths to return when orienting the graph (note: paths
  may contain duplicate vertices, but never duplicate edges.)
* local_search: a boolean parameter that enables MEO's local search functionality. See "Improving approximations with local search" in
  the associated paper for more information. This should almost always be true.
* rand_restarts: the number (int) of random restarts to use.
