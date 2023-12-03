import json
import os
from typing import Tuple, Union

import networkx as nx
import pandas as pd
from graphspace_python.api.client import GraphSpace
from graphspace_python.graphs.classes.gsgraph import GSGraph


def write_json(graph_file,out_graph,out_style) -> None:

    # get GS Graph
    graph_name = os.path.basename(out_graph) # name is the prefix specified.
    G = get_gs_graph(graph_file, graph_name)

    # write graph JSON
    with open(out_graph,'w') as f:
        json.dump(G.get_graph_json(),f)

    # write graph style JSON
    with open(out_style,'w') as f:
        json.dump(G.get_style_json(),f)
    return


def post_graph(G:GSGraph,username:str,password:str) -> None:
    """
    Post a graph to GraphSpace.
    We need to resolve the issue with username/password in config
    files before we post to GraphSpace.
    """
    gs = GraphSpace(username,password)
    try:
        gs.update_graph(G)
    except:
        gs.post_graph(G)
    print('posted graph')
    return


def get_gs_graph(graph_file:str,graph_name:str) -> GSGraph:
    """
    Creates a GraphSpace graph using the networkx graph or digraph and directionality returned from load_graph

    If the graph is empty, that likely means the graph was mixed in directionality
    - this will return an empty GraphSpace graph
    """
    # read file as networkx graph
    # returns a tuple, (the graph, directionality)
    nxG, directed = load_graph(graph_file)

    # convert networkx graph to GraphSpace object
    G = GSGraph()
    G.set_name(graph_name)
    for n in nxG.nodes():
        G.add_node(n,label=n,popup='Node %s' % (n))
        G.add_node_style(n,color='#ACCE9A',shape='rectangle',width=30,height=30)
    for u,v in nxG.edges():
        if directed:
            G.add_edge(u,v,directed=True,popup='Directed Edge %s-%s<br>Rank %d' % (u,v,nxG[u][v]['Rank']))
            G.add_edge_style(u,v,directed=True,width=2,color='#281D6A')
        else:
            G.add_edge(u,v,popup='Undirected Edge %s-%s<br>Rank %d' % (u,v,nxG[u][v]['Rank']))
            G.add_edge_style(u,v,width=2,color='#281D6A')
    return G


def load_graph(path: str) -> Tuple[Union[nx.Graph, nx.DiGraph], bool]:
    """
    Returns a Graph or Digraph, accompanied by a boolean indicating if it's directed.

    This code is compatible only with fully directed or undirected graphs.
    If neither, an empty Graph will be returned
    """
    G = nx.Graph()
    directed = False

    try:
        pathways = pd.read_csv(path, sep="\t", header=None)
    except pd.errors.EmptyDataError:
        print(f"The file {path} is empty.")
        return G, directed
    pathways.columns = ["Interactor1", "Interactor2", "Rank", "Direction"]
    mask_u = pathways['Direction'] == 'U'
    mask_d = pathways['Direction'] == 'D'
    pathways.drop(columns=["Direction"])

    if mask_u.all():
        G = nx.from_pandas_edgelist(pathways, "Interactor1", "Interactor2", ["Rank"])
        directed = False

    elif mask_d.all():
        G = nx.from_pandas_edgelist(pathways, "Interactor1", "Interactor2", ["Rank"], create_using=nx.DiGraph())
        directed = True
    else:
        print(f"{path} could not be visualized. GraphSpace does not support mixed direction type graphs currently")

    return G, directed
