import sys
import networkx as nx
import os
import pandas as pd
#wrapper functions for nx methods here


# TODO complete the docstring
def summarize_networks(file_paths, node_table):
    """

    @param file_paths:
    @param node_table:
    @return:
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
        nw = nx.read_weighted_edgelist(file_path)
        # Save the network name, number of nodes, number edges, and number of connected components
        # TODO Decide how to represent the pathway name in the table, in the workflow pathways have the same basename
        nw_name = str(file_path)
        #nw_name = os.path.basename(file_path)
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
    nw_info = pd.DataFrame(
        nw_info,
        columns = [
            "Name",
            "Number of nodes",
            "Number of edges",
            "Number of connected components"
            ]
        +
        nodes_by_col_labs
    )
    return nw_info


def degree(G):
    return dict(G.degree)

#stats is just a list of functions to apply to the graph. They should take as input a networkx graph or digraph but may have any output.
stats = [degree,nx.clustering,nx.betweenness_centrality]

def produce_statistics(G: nx.Graph,s=None) -> dict:
    global stats
    if s != None:
        stats = s
    d = dict()
    for s in stats:
        sname = s.__name__
        d[sname] = s(G)
    return d

def load_graph(path: str,directed=False) -> nx.Graph:
    #try:
    if not directed:
        G = nx.read_edgelist(path,data=(('rank',float),))
    else:
        # note - self-edges are not allowed in DiGraphs.
        G = nx.read_edgelist(path,data=(('rank',float),),create_using=nx.DiGraph)
    #except:
    #    print('file format not yet supported. submit a feature request if it ought to be!')
    return G

def save_json(data,pth):
    with open(pth,'w') as f:
        json.dump(data,f)

def save(data,pth):
    fout = open (pth,'w')
    fout.write('#node\t%s\n' % '\t'.join([s.__name__ for s in stats]))
    for node in data[stats[0].__name__]:
        row = [data[s.__name__][node] for s in stats]
        fout.write('%s\t%s\n'% (node,'\t'.join([str(d) for d in row])))
    fout.close()

'''
run function that wraps above functions.
'''
def run(infile:str,outfile:str,directed=False) -> None:
    ## if output directory doesn't exist, make it.
    outdir = os.path.dirname(outfile)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    ## load graph, produce stats, and write to human-readable file.
    G = load_graph(infile,directed=directed)
    dat = produce_statistics(G)
    save(dat,outfile)

    return


'''
for testing
'''
def main(argv):
    G = load_graph(argv[1])
    print(G.nodes)
    dat = produce_statistics(G)
    print(dat)
    save(dat,argv[2])


if __name__ == "__main__":
    main(sys.argv)
