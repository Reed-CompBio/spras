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
    parser.add_argument("--sources", type=Path, required=True, help="Path to the source nodes file")
    parser.add_argument("--targets", type=Path, required=True, help="Path to the target nodes file")
    parser.add_argument("--output", type=Path, required=True, help="Path to the output file that will be written")
    parser.add_argument("--alpha", type=float, required=False, default=0.85, help="Optional alpha value for the RWR algorithm (defaults to 0.85)")

    return parser.parse_args()


def RWR(network_file: Path, source_nodes_file: Path,target_nodes_file: Path, alpha: float, output_file: Path):
    if not network_file.exists():
        raise OSError(f"Network file {str(network_file)} does not exist")
    if not source_nodes_file.exists():
        raise OSError(f"Nodes file {str(source_nodes_file)} does not exist")
    if not target_nodes_file.exists():
        raise OSError(f"Nodes file {str(target_nodes_file)} does not exist")
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

    # Read in sources file
    sources = []
    with open(source_nodes_file) as source_nodes:
        for line in source_nodes:
            source = line.split('\t')
            sources.append(source[0].strip('\n'))

    # Read in targets file
    targets = []
    with open(target_nodes_file) as target_nodes:
        for line in target_nodes:
            target = line.split('\t')
            targets.append(target[0].strip('\n'))

    # Create directed graph from input network
    source_graph = nx.DiGraph(edgelist)

    # Create reversed graph to run pagerank on targets
    target_graph = source_graph.reverse(copy= True)

    # Run pagegrank algorithm on source and target graph seperatly
    source_scores = nx.pagerank(source_graph,personalization={n:1 for n in sources},alpha=alpha)
    target_scores = nx.pagerank(target_graph,personalization={n:1 for n in targets},alpha=alpha)

    # Merge scores from source and target pagerank runs
    # While merge_scores currently returns the average of the two scores, alternate methods such as taking
    # the minimum of the two scores may be used
    total_scores = merge_scores(source_scores,target_scores)

    with output_file.open('w') as output_f:
        output_f.write("Node\tScore\n")
        node_scores = list(total_scores.items())
        node_scores.sort(reverse=True,key=lambda kv: (kv[1], kv[0]))
        for node in node_scores:
            #todo: filter scores based on threshold value
                output_f.write(f"{node[0]}\t{node[1]}\n")
    return

def merge_scores(sources,targets):
    output = {}
    nodes = sources.keys()
    for node in nodes:
        output.update({node:((sources.get(node)+targets.get(node))/2)})
    return output


def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    RWR(args.network, args.sources, args.targets, args.alpha, args.output)


if __name__ == "__main__":
    main()
