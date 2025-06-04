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
    parser.add_argument("--alpha", type=float, required=False, help="Optional alpha value for the RWR algorithm (defaults to 0.85)")

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

    # Create the parent directories for the output file if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    edgelist = []
    with open(network_file) as file:
         for line in file:
            edge = line.split('|')
            edge[1] = edge[1].strip('\n')
            edgelist.append(edge)
    
    sources = []
    with open(source_nodes_file) as source_nodes:
        for line in source_nodes:
            source = line.split('\t')
            sources.append(source[0].strip('\n'))

    targets = []
    with open(target_nodes_file) as target_nodes:
        for line in target_nodes:
            target = line.split('\t')
            targets.append(target[0].strip('\n'))

    source_graph = nx.DiGraph(edgelist)
    target_graph = source_graph.reverse(copy= True)

    source_scores = nx.pagerank(source_graph,personalization=add_ST(sources),alpha=alpha)
    target_scores = nx.pagerank(target_graph,personalization=add_ST(targets),alpha=alpha)
    total_scores = merge_scores(source_scores,target_scores)


#todo: threshold should to be adjusted automatically 
    with output_file.open('w') as output_f:
        for node in total_scores.keys():
            if total_scores.get(node) > 0.1:
                for edge in edgelist:
                    if node in edge[0] or node in edge[1]:
                        output_f.write(f"{edge[0]}\t{edge[1]}\n")

def merge_scores(sources,targets):
    output = {}
    nodes = sources.keys()
    for node in nodes:
        output.update({node:((sources.get(node)+targets.get(node))/2)})
    return output

def add_ST(nodes):
    output = {}
    for node in nodes:
        output.update({node:1})
    return output



def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    RWR(args.network, args.sources, args.targets, args.alpha, args.output)


if __name__ == "__main__":
    main()