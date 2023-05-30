import networkx as nx
import random
import numpy as np

# Add directed edges in graph


def add_edges(g, pr):
	for each in g.nodes():
		for each1 in g.nodes():
			if (each != each1):
				ra = random.random()
				if (ra < pr):
					g.add_edge(each, each1)
				else:
					continue
	return g

# Sort the nodes


def nodes_sorted(g, points):
	t = np.array(points)
	t = np.argsort(-t)
	return t

# Distribute points randomly in a graph


def random_Walk(g):
	rwp = [0 for i in range(g.number_of_nodes())]
	nodes = list(g.nodes())
	r = random.choice(nodes)
	rwp[r] += 1
	neigh = list(g.out_edges(r))
	z = 0

	while (z != 10000):
		if (len(neigh) == 0):
			focus = random.choice(nodes)
		else:
			r1 = random.choice(neigh)
			focus = r1[1]
		rwp[focus] += 1
		neigh = list(g.out_edges(focus))
		z += 1
	return rwp


def ppr(G, S: list, beta=0.85):
	rwp = {}
	for i in G.nodes():
		rwp[i] = 0
	print(rwp)
	nodes = list(G.nodes())
	source_node = random.choice(S)
	rwp[source_node] += 1
	neigh = list(G.out_edges(source_node))
	z = 0

	while (z != 10000):
		if (len(neigh) == 0):
			focus = random.choice(nodes)
		else:
			r1 = random.choice(neigh)
			focus = r1[1]
		rwp[focus] += 1
		neigh = list(G.out_edges(focus))
		z += 1


# Main
# 1. Create a directed graph with N nodes
G = nx.barabasi_albert_graph(60, 41)
pr = nx.pagerank(G)
print(pr)

g = nx.DiGraph()
N = 15
g.add_nodes_from(range(N))

# 2. Add directed edges in graph
g = add_edges(g, 0.4)


ppr(g, [1, 2, 3], 0.4)


# # 3. perform a random walk
# points = random_Walk(g)

# # 4. Get nodes rank according to their random walk points
# sorted_by_points = nodes_sorted(g, points)
# print("PageRank using Random Walk Method")
# print(sorted_by_points)

# # p_dict is dictionary of tuples
# p_dict = nx.pagerank(g)
# p_sort = sorted(p_dict.items(), key=lambda x: x[1], reverse=True)

# print("PageRank using inbuilt pagerank method")
# for i in p_sort:
#     print(i[0], end=", ")
