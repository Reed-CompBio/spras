import networkx as nx

"""
Local neighborhood pathway reconstruction algorithm.
The algorithm takes a network and a list of nodes as input.
It outputs all edges in the network that have a node from the list as an endpoint.
"""

import argparse
from pathlib import Path

'''
--edges_file 
format:
Node1 Node2 Weight
A B 0.5
B C 0.6
D E 0.7
E A 0.8
...

--sources_file 
NODEID  Prizes(Not implement right now; maybe later)
A
B
C
...

--targets_file (same format as sources_file) 
--relevance_function(default: random_walk) (options: random_walk, HotNet)
--selection_function(default: min)
# --alpha(default: 0.01)
--output_nodes
--output_edges
'''


def parse_arguments():
    """
    Process command line arguments.
    @return arguments
    """
    parser = argparse.ArgumentParser(
        description="Random Walk path reconstruction"
    )
    parser.add_argument("--edges_file", type=Path, required=True, help="Path to the edges file")
    parser.add_argument("--sources_file", type=Path, required=True, help="Path to the source node file")
    parser.add_argument("--targets_file", type=Path, required=True, help="Path to the target node file")
    parser.add_argument("--relevance_function(default: pagerank)", type=str, required= True, default='r' ,help="Select a relevance function to use (r for random walk/h for HotNet)")
    parser.add_argument("--selection_function", type=str, required= True, default= 'min', help="Select a function to use (min for minimum/sum for sum)")
    # parser.add_argument("--alpha", type=float, required= True, default= 0.01, help="Select the alpha value for the random walk")
    parser.add_argument("--output_nodes", type=Path, required=True, help="Path to the output file for nodes")
    parser.add_argument("--output_edges", type=Path, required=True, help="Path to the output file for edges")

    return parser.parse_args()

# Utility functions
def generate_nodes_and_edges(edges_file: Path) -> tuple(set, list):
    nodes = set()
    edges = []
    with edges_file.open() as edges_f:
        for i, line in enumerate(edges_f):
            # if the first line is the title, skip it
            if i == 0:
                continue
            line = line.strip()
            endpoints = line.split(" ")
            if len(endpoints) != 3:
                raise ValueError(f"Edge {line} does not contain 2 nodes separated by ' ' and a weight")
            nodes.add(endpoints[0])
            nodes.add(endpoints[1])
            edges.append((endpoints[0], endpoints[1], endpoints[2]))
    return nodes, edges

def generate_nodes(nodes_file: Path) -> list:
    nodes = []
    with nodes_file.open() as nodes_f:
        for i, line in enumerate(nodes_f):
            # if the first line is the title, skip it
            if i == 0:
                continue
            nodes.append(line.strip())
    return nodes

def generate_edges(edges_file: Path) -> list:
    edges = []
    with edges_file.open() as edges_f:
        for line in edges_f:
            line = line.strip()
            endpoints = line.split(" ")
            if len(endpoints) != 3:
                raise ValueError(f"Edge {line} does not contain 2 nodes separated by ' ' and a weight")
            edges.append((endpoints[0], endpoints[1], endpoints[2]))
    return edges


def generate_graph(nodes, edges) -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)
    return G

def generate_personalization_vector(nodes : list) -> dict:
    personalization_vector = {}
    # assigning value 1 to the source and target nodes to pass it to the random walk function
    for i in nodes:
        personalization_vector[i] = 1
    
    return personalization_vector

def generate_output_nodes(nodes: list, output_file: Path):
    pass

def generate_output_edges(edges: list, output_file: Path):
    pass


# main algorithm
def random_walk(edges_file: Path, sources_file: Path, targets_file: Path, relevance_function: str, selection_function: str, output_nodes_file: Path, output_edges_file: Path):
    if not edges_file.exists():
        raise OSError(f"Edges file {str(edges_file)} does not exist")
    if not sources_file.exists():
        raise OSError(f"Sources file {str(sources_file)} does not exist")
    if not targets_file.exists():
        raise OSError(f"Targets file {str(targets_file)} does not exist")
    
    if output_nodes_file.exists():
        print(f"Output files {str(output_nodes_file)} (nodes) will be overwritten")
    if output_edges_file.exists():
        print(f"Output files {str(output_edges_file)} (edges) will be overwritten")

    # Create the parent directories for the output file if needed
    output_nodes_file.parent.mkdir(parents=True, exist_ok=True)
    output_edges_file.parent.mkdir(parents=True, exist_ok=True)

    # Read the list of sources
    G = generate_graph(generate_nodes_and_edges(edges_file)[0], generate_nodes_and_edges(edges_file)[1])
    source_node = generate_nodes(sources_file)
    pr = nx.pagerank(G, alpha=0.85, personalization=generate_personalization_vector(source_node))
    
    R = G.reverse()
    target_node = generate_nodes(targets_file)
    r_pr = nx.pagerank(R, alpha=0.85, personalization=generate_personalization_vector(target_node))

    final_pr = {}
    for i in pr:
        final_pr[i] = min(pr[i], r_pr[i])
    

    with output_nodes_file.open('w') as output_f:
        pass
    print()
    
    with output_edges_file.open('w') as output_f:
        pass
    print()


def main():
    """
    Parse arguments and run pathway reconstruction
    """
    args = parse_arguments()
    local_neighborhood(args.network, args.nodes, args.output)


if __name__ == "__main__":
    main()

