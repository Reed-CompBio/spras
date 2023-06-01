# Read the list of sources
from pathlib import Path
import networkx as nx

edges_file = Path("./input/edges.txt")
source_file = Path("./input/source_nodes.txt")
target_file = Path("./input/target_nodes.txt")

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

final_pr = {}
for i in pr:
    final_pr[i] = min(pr[i], r_pr[i])

print(final_pr)    
# for each node : node, pr, r_pr, final_pr
output_nodes_file = Path("./output/output_nodes.txt")
output_edges_file = Path("./output/output_edges.txt")

with output_nodes_file.open("w") as output_nodes_f:
    output_nodes_f.write("node pr r_pr final_pr\n")
    for i in final_pr:
        output_nodes_f.write(f"{i} {pr[i]} {r_pr[i]} {final_pr[i]}\n")

def generate_output_edges(G: nx.DiGraph, pr : dict, output_edges_file: Path):
    edge_sum = {}
    for node in G.nodes():
        temp = 0
        for i in G.out_edges(node):
            temp += float(G[node][i[1]]['weight'])
        edge_sum[node] = temp
        
    print(edge_sum)

    edge_flux = {}
    #calculate the edge flux
    for edge in G.edges():
        print(edge)
        edge_flux[edge] = pr[edge[0]] * float(G[edge[0]][edge[1]]['weight']) / edge_sum[edge[0]]

    print(edge_flux)

    with output_edges_file.open("w") as output_edges_f:
        output_edges_f.write("Node1 Node2 Weight\n")
        for i in edge_flux:
            output_edges_f.write(f"{i[0]} {i[1]} {edge_flux[i]}\n")
            
generate_output_edges(G,final_pr,output_edges_file)
# get a list of edges 
'''
using edge flux
'''