"""
Local neighborhood pathway reconstruction algorithm.
The algorithm takes a network and a list of nodes as input.
It outputs all edges in the network that have a node from the list as an endpoint.
"""

import argparse
from pathlib import Path


def parse_arguments():
    """
    Process command line arguments.
    @return arguments
    """
    parser = argparse.ArgumentParser(
        description="Local neighborhood pathway reconstruction"
    )
    parser.add_argument("--network", type=Path, required=True, help="Path to the network file with '|' delimited node pairs")
    parser.add_argument("--nodes", type=Path, required=True, help="Path to the nodes file")
    parser.add_argument("--output", type=Path, required=True, help="Path to the output file that will be written")

    return parser.parse_args()


def local_neighborhood(network_file: Path, nodes_file: Path, output_file: Path):
    if not network_file.exists():
        raise OSError(f"Network file {str(network_file)} does not exist")
    if not nodes_file.exists():
        raise OSError(f"Nodes file {str(nodes_file)} does not exist")
    if output_file.exists():
        print(f"Output file {str(output_file)} will be overwritten")

    # Create the parent directories for the output file if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Read the list of nodes
    nodes = set()
    with nodes_file.open() as nodes_f:
        for line in nodes_f:
            nodes.add(line.strip())
    print(f"Read {len(nodes)} unique nodes")

    # Iterate through the network edges and write those that have an endpoint in the node set
    in_edge_counter = 0
    out_edge_counter = 0
    with output_file.open('w') as output_f:
        with network_file.open() as network_f:
            for line in network_f:
                line = line.strip()
                in_edge_counter += 1
                endpoints = line.split("|")
                if len(endpoints) != 2:
                    raise ValueError(f"Edge {line} does not contain 2 nodes separated by '|'")
                if endpoints[0] in nodes or endpoints[1] in nodes:
                    out_edge_counter += 1
                    output_f.write(f"{line}\n")
    print(f"Kept {out_edge_counter} of {in_edge_counter} edges")


def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    local_neighborhood(args.network, args.nodes, args.output)


if __name__ == "__main__":
    main()
