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
        description="AllPairs pathway reconstruction"
    )
    parser.add_argument("--network", type=Path, required=True, help="Path to the network file with '|' delimited node pairs")
    parser.add_argument("--nodes", type=Path, required=True, help="Path to the nodes file")
    parser.add_argument("--output", type=Path, required=True, help="Path to the output file that will be written")

    return parser.parse_args()


def allpairs(network_file: Path, nodes_file: Path, output_file: Path):
    if not network_file.exists():
        raise OSError(f"Network file {str(network_file)} does not exist")
    if not nodes_file.exists():
        raise OSError(f"Nodes file {str(nodes_file)} does not exist")
    if output_file.exists():
        print(f"Output files {str(output_file)} will be overwritten")

    # Create the parent directories for the output file if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Read the list of nodes
    nodes = set()
    with nodes_file.open() as nodes_f:
        for line in nodes_f:
            nodes.add(line.strip())
    print(f"Read {len(nodes)} unique nodes")

    path = nx.all_pairs_shortest_path(network_file, cutoff=None)
    print(path)
    nx.write_edgelist(path, output_file)
    print(f"Wrote output file to {str(output_file)}")


def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    allpairs(args.network, args.nodes, args.output)


if __name__ == "__main__":
    main()
