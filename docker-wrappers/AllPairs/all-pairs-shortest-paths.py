"""
All Pairs Shortest Paths pathway reconstruction algorithm.
The algorithm takes a network and a list of sources and targets as input.
It outputs the shortest possible path between every source and every target.
"""

import argparse
from pathlib import Path

import networkx as nx


def parse_arguments():
    """
    Process command line arguments.
    @return arguments
    """
    parser = argparse.ArgumentParser(
        description="All Pairs Shortest Paths pathway reconstruction"
    )
    parser.add_argument("--network", type=Path, required=True, help="Network file of the form <node1> <node2> <weight>."
                                                                    " Tab-delimited.")
    parser.add_argument("--nodes", type=Path, required=True, help="Nodes file of the form <node> <source-or-target>. "
                                                                  "Tab-delimited.")
    parser.add_argument("--output", type=Path, required=True, help="Output file")

    return parser.parse_args()


def allpairs(network_file: Path, nodes_file: Path, output_file: Path):
    if not network_file.exists():
        raise OSError(f"Network file {str(network_file)} does not exist")
    if not nodes_file.exists():
        raise OSError(f"Nodes file {str(nodes_file)} does not exist")
    if output_file.exists():
        print(f"Output file {str(output_file)} will be overwritten")

    # Create the parent directories for the output file if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Read the list of nodes
    sources = set()
    targets = set()
    with nodes_file.open() as nodes_f:
        for line in nodes_f:
            row = line.strip().split(sep='\t')
            if row[1] == 'source':
                sources.add(row[0])
            elif row[1] == 'target':
                targets.add(row[0])

    # There should be at least one source and one target
    assert len(sources) > 0, 'There are no sources.'
    assert len(targets) > 0, 'There are no targets.'

    # Read graph & assert all the sources/targets are in network
    graph = nx.read_weighted_edgelist(network_file, delimiter='\t')
    assert len(sources.intersection(graph.nodes())) == len(sources), 'At least one source is not in the interactome.'
    assert len(targets.intersection(graph.nodes())) == len(targets), 'At least one target is not in the interactome.'

    # Finally, compute all-pairs-shortest-paths and record the subgraph.
    output = nx.Graph()
    for source in sources:
        for target in targets:
            p = nx.shortest_path(graph, source, target, weight='weight')
            nx.add_path(output, p)

    # Write the subgraph as a list of edges.
    nx.write_edgelist(output, output_file, data=False, delimiter='\t')
    print(f"Wrote output file to {str(output_file)}")


def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    allpairs(args.network, args.nodes, args.output)


if __name__ == "__main__":
    main()
