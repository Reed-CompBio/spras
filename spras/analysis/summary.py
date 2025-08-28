from collections import OrderedDict
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import networkx as nx
import pandas as pd


def summarize_networks(file_paths: Iterable[Path], node_table: pd.DataFrame, algo_params: dict[str, dict[str, dict]],
                       algo_with_params: list) -> pd.DataFrame:
    """
    Generate a table that aggregates summary information about networks in file_paths, including which nodes are present
    in node_table columns. Network directionality is ignored and all edges are treated as undirected. The order of the
    file_paths and algo_with_params inputs must match after they are each sorted.
    @param file_paths: iterable of edge list files
    @param node_table: pandas DataFrame containing node attributes
    @param algo_params: a nested dict mapping algorithm names to dicts that map parameter hashes to parameter
    combinations.
    @param algo_with_params: a list of <algorithm>-params-<params_hash> combinations
    @return: pandas DataFrame with summary information
    """
    # Ensure that NODEID is the first column
    assert node_table.columns[0] == 'NODEID'
    # Initialize list to store input nodes that have property data
    nodes_by_col = []
    # Save new labels
    nodes_by_col_labs = ('Nodes in ' + node_table.columns[1:]).tolist()
    # Iterate through each node property column
    for col in node_table.columns[1:]:
        # Assumption: property columns only contain NA, boolean, numeric data
        # If the property contains numeric data, save the nodes with property values that are not NA and > 0
        # If the property contains boolean data, save the nodes with property values that are True
        nodes_by_col.append(set(node_table.loc[node_table[col] > 0, 'NODEID']))

    # Initialize list to store network summary data
    nw_info: list[list[Any]] = []

    algo_with_params = sorted(algo_with_params)

    # Iterate through each network file path
    for index, file_path in enumerate(sorted(file_paths)):
        with open(file_path, 'r') as f:
            lines = f.readlines()[1:] # as this is an output edge file, we skip the header line

        # directed or mixed graphs are parsed and summarized as an undirected graph
        nw = nx.read_edgelist(lines, data=(('weight', float), ('Direction', str)))

        # Begin collecting data into a dictionary.
        # (We use dictionaries over list to make )
        data: OrderedDict[str, Any] = OrderedDict()

        data.update([
            ('Name', str(file_path)),
            ('Number of nodes', nw.number_of_nodes()),
            ('Number of edges', nw.number_of_edges()),
            ('Number of connected components', nx.number_connected_components(nw)),
        ])

        # Save the max/median degree, average clustering coefficient, and density
        degrees = [deg for _, deg in nw.degree()]
        data.update([
            # If the number of nodes are 0, degrees will equal [],
            # making the following statistics all be zero.
            ('Density', nx.density(nw)),
            ('Max degree', max(degrees, default=0)),
            ('Median degree', median(degrees or [0])),
        ])

        cc = list(nx.connected_components(nw))
        # Save the max diameter
        # Use diameter only for components with ≥2 nodes (singleton components have diameter 0)
        diameters = [
            nx.diameter(nw.subgraph(c).copy()) if len(c) > 1 else 0
            for c in cc
        ]
        data['Max diameter'] = max(diameters, default=0)

        # Save the average path lengths
        # Compute average shortest path length only for components with ≥2 nodes (undefined for singletons, set to 0.0)
        avg_path_lengths = [
            nx.average_shortest_path_length(nw.subgraph(c).copy()) if len(c) > 1 else 0.0
            for c in cc
        ]
        if len(avg_path_lengths) != 0:
            data['Average path length'] = sum(avg_path_lengths) / len(avg_path_lengths)
        else:
            data['Average path length'] = 0.0

        # Initialize list to store current network information
        current_network_info = list(data.values())

        # Iterate through each node property and save the intersection with the current network
        for node_list in nodes_by_col:
            num_nodes = len(set(nw).intersection(node_list))
            current_network_info.append(num_nodes)

        # String split to access algorithm and hashcode: <algorithm>-params-<params_hash>
        parts = algo_with_params[index].split('-')
        algo = parts[0]
        hashcode = parts[2]

        # Algorithm parameters have format { algo : { hashcode : { parameter combos } } }
        param_combo = algo_params[algo][hashcode]
        current_network_info.append(param_combo)

        # Save the current network information to the network summary list
        nw_info.append(current_network_info)

    # Prepare column names
    col_names = ['Name', 'Number of nodes', 'Number of edges', 'Number of connected components', 'Density', 'Max degree', 'Median degree', 'Max diameter', 'Average path length']
    col_names.extend(nodes_by_col_labs)
    col_names.append('Parameter combination')

    # Convert the network summary data to pandas dataframe
    nw_df = pd.DataFrame(
        nw_info,
        columns=col_names
    )

    return nw_df


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


# if __name__ == '__main__':
#     main(sys.argv)
