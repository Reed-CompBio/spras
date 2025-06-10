import argparse
from pathlib import Path
import networkx as nx

def parse_arguments():
    """
    Process command line arguments.
    @return arguments
    """
    parser = argparse.ArgumentParser(
        description="Random walk with restarts pathway reconstruction"
    )
    parser.add_argument("--network", type=Path, required=True, help="Path to the network file with '|' delimited node pairs")
    parser.add_argument("--nodes", type=Path, required=True, help="Path to the nodes file")
    parser.add_argument("--output", type=Path, required=True, help="Path to the output file that will be written")
    parser.add_argument("--alpha", type=float, required=False, default=0.85, help="Optional alpha value for the RWR algorithm (defaults to 0.85)")

    return parser.parse_args()


def RWR(network_file: Path, nodes_file: Path, alpha: float, output_file: Path):
    if not network_file.exists():
        raise OSError(f"Network file {str(network_file)} does not exist")
    if not nodes_file.exists():
        raise OSError(f"Nodes file {str(nodes_file)} does not exist")
    if output_file.exists():
        print(f"Output file {str(output_file)} will be overwritten")
    if not alpha > 0 or not alpha <=1:
        raise ValueError("Alpha value must be between 0 and 1")

    # Create the parent directories for the output file if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Read in network file
    edgelist = []
    with open(network_file) as file:
         for line in file:
            edge = line.split('|')
            edge[1] = edge[1].strip('\n')
            edgelist.append(edge)

    # Read in node file (combined sources and targets)
    nodelist = []
    with open(nodes_file) as n_file:
        for line in n_file:
            node = line.split('\t')
            nodelist.append(node[0].strip('\n'))

    # Create directed graph from input network
    graph = nx.DiGraph(edgelist)

    # Run pagerank algorithm on directed graph
    scores = nx.pagerank(graph,personalization={n:1 for n in nodelist},alpha=alpha)


    with output_file.open('w') as output_f:
        output_f.write("Node\tScore\n")
        node_scores = list(scores.items())
        node_scores.sort(reverse=True,key=lambda kv: (kv[1], kv[0]))
        for node in node_scores:
            #todo: filter scores based on threshold value
                output_f.write(f"{node[0]}\t{node[1]}\n")
    return


def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    RWR(args.network, args.nodes, args.alpha, args.output)


if __name__ == "__main__":
    main()