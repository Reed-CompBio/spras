import os
import sys
from pathlib import Path
from typing import Iterable

import networkx as nx
import pandas as pd


def summarize_networks(file_paths: Iterable[Path], node_table: pd.DataFrame) -> pd.DataFrame:
    """
    Generate a table that aggregates summary information about networks in file_paths,
    including which nodes are present in node_table columns.
    @param file_paths: iterable of edge list files
    @param node_table: pandas DataFrame containing node attributes
    @return: pandas DataFrame with summary information
    """
    # Ensure that NODEID is the first column
    assert node_table.columns[0] == "NODEID"
    # Initialize list to store input nodes that have property data
    nodes_by_col = []
    # Save new labels
    nodes_by_col_labs = ("Nodes in " + node_table.columns[1:]).tolist()
    # Iterate through each node property column
    for col in node_table.columns[1:]:
        # Assumption: property columns only contain NA, boolean, numeric data
        # If the property contains numeric data, save the nodes with property values that are not NA and > 0
        # If the property contains boolean data, save the nodes with property values that are True
        nodes_by_col.append(set(node_table.loc[node_table[col] > 0, "NODEID"]))

    # Initialize list to store network summary data
    nw_info = []

    # Iterate through each network file path
    for file_path in sorted(file_paths):
        # Load in the network
        nw = nx.read_edgelist(file_path, data=(('weight', float), ('Direction',str)))
        # Save the network name, number of nodes, number edges, and number of connected components
        nw_name = str(file_path)
        number_nodes = nw.number_of_nodes()
        number_edges = nw.number_of_edges()
        ncc = nx.number_connected_components(nw)
        # Initialize list to store current network information
        cur_nw_info = [nw_name, number_nodes, number_edges, ncc]
        # Iterate through each node property and save the intersection with the current network
        for node_list in nodes_by_col:
            num_nodes = len(set(nw).intersection(node_list))
            cur_nw_info.append(num_nodes)
        # Save the current network information to the network summary list
        nw_info.append(cur_nw_info)

    # Convert the network summary data to pandas dataframe
    # Could refactor to create the dataframe line by line instead of storing data as lists and then converting
    nw_info = pd.DataFrame(
        nw_info,
        columns=[
                    "Name",
                    "Number of nodes",
                    "Number of undirected edges",
                    "Number of connected components"
                ]
                +
                nodes_by_col_labs
    )
    return nw_info


def degree(g):
    return dict(g.degree)

# TODO: redo .run code to work on mixed graphs
# stats is just a list of functions to apply to the graph.
# They should take as input a networkx graph or digraph but may have any output.
# stats = [degree, nx.clustering, nx.betweenness_centrality]


# def produce_statistics(g: nx.Graph, s=None) -> dict:
#     global stats
#     if s is not None:
#         stats = s
#     d = dict()
#     for s in stats:
#         sname = s.__name__
#         d[sname] = s(g)
#     return d


# def load_graph(path: str) -> nx.Graph:
#     g = nx.read_edgelist(path, data=(('weight', float), ('Direction',str)))
#     return g


# def save(data, pth):
#     fout = open(pth, 'w')
#     fout.write('#node\t%s\n' % '\t'.join([s.__name__ for s in stats]))
#     for node in data[stats[0].__name__]:
#         row = [data[s.__name__][node] for s in stats]
#         fout.write('%s\t%s\n' % (node, '\t'.join([str(d) for d in row])))
#     fout.close()


# def run(infile: str, outfile: str) -> None:
#     """
#     run function that wraps above functions.
#     """
#     # if output directory doesn't exist, make it.
#     outdir = os.path.dirname(outfile)
#     if not os.path.exists(outdir):
#         os.makedirs(outdir)

#     # load graph, produce stats, and write to human-readable file.
#     g = load_graph(infile)
#     dat = produce_statistics(g)
#     save(dat, outfile)


# def main(argv):
#     """
#     for testing
#     """
#     g = load_graph(argv[1])
#     print(g.nodes)
#     dat = produce_statistics(g)
#     print(dat)
#     save(dat, argv[2])


# if __name__ == "__main__":
#     main(sys.argv)
