# Read the list of sources
from pathlib import Path
import networkx as nx

edges_file = Path("./edges.txt")
source_file = Path("./source_nodes.txt")
target_file = Path("./target_nodes.txt")

def generate_nodes_and_edges(edges_file: Path) -> tuple:
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


G = generate_graph(generate_nodes_and_edges(edges_file)[0], generate_nodes_and_edges(edges_file)[1])
source_node = generate_nodes(source_file)
pr = nx.pagerank(G, alpha=0.85, personalization=generate_personalization_vector(source_node))

R = G.reverse()
target_node = generate_nodes(target_file)
r_pr = nx.pagerank(R, alpha=0.85, personalization=generate_personalization_vector(target_node))

ans = {}
for i in pr:
    ans[i] = min(pr[i], r_pr[i])

print(ans)    
# for each node : node, pr, r_pr, final_pr

# get a list of edges 
'''
using edge flux
'''