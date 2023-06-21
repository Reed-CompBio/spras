import json
import os
import sys

import networkx as nx
from graphspace_python.api.client import GraphSpace
from graphspace_python.graphs.classes.gsgraph import GSGraph


def write_json(graph_file,out_graph,out_style,directed=False) -> None:

	# get GS Graph
	graph_name = os.path.basename(out_graph) # name is the prefix specified.
	G = get_gs_graph(graph_file,graph_name,directed=directed)

	# write graph JSON
	with open(out_graph,'w') as f:
		json.dump(G.get_graph_json(),f)

	# write graph style JSON
	with open(out_style,'w') as f:
		json.dump(G.get_style_json(),f)
	return

'''
Post a graph to GraphSpace.
We need to resolve the issue with username/password in config
files before we post to GraphSpace.
'''
def post_graph(G:GSGraph,username:str,password:str,directed=False) -> None:
	gs = GraphSpace(username,password)
	try:
		gs.update_graph(G)
	except:
		gs.post_graph(G)
	print('posted graph')
	return

def get_gs_graph(graph_file:str,graph_name:str,directed=False) -> GSGraph:
	# read file as networkx graph
	nxG = load_graph(graph_file,directed=directed)

	# convert networkx graph to GraphSpace object
	G = GSGraph()
	G.set_name(graph_name)
	for n in nxG.nodes():
		G.add_node(n,label=n,popup='Node %s' % (n))
		G.add_node_style(n,color='#ACCE9A',shape='rectangle',width=30,height=30)
	for u,v in nxG.edges():
		if directed:
			G.add_edge(u,v,directed=True,popup='Directed Edge %s-%s<br>Rank %d' % (u,v,nxG[u][v]['rank']))
			G.add_edge_style(u,v,directed=True,width=2,color='#281D6A')
		else:
			G.add_edge(u,v,popup='Undirected Edge %s-%s<br>Rank %d' % (u,v,nxG[u][v]['rank']))
			G.add_edge_style(u,v,width=2,color='#281D6A')
	return G

## TODO this is a duplicated function in summary.py.
## Pull this and others into a utils.py function.
def load_graph(path: str,directed=False) -> nx.Graph:
	if not directed:
		G = nx.read_edgelist(path,data=(('rank',float),))
	else:
		# note - self-edges are not allowed in DiGraphs.
		G = nx.read_edgelist(path,data=(('rank',float),),create_using=nx.DiGraph)
	return G
