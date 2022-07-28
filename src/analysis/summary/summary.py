import sys
import networkx as nx
import os
import pandas as pd
#import json
#wrapper functions for nx methods here

def summarize_networks(file_paths, node_table):    
    # Initialize list to store input nodes that have property data
    nodes_by_col = []
    # Save new labels
    nodes_by_col_labs = ("nodes in " + node_table.columns[1:]).tolist()
    # Iterate through each node property column
    for node_property in range(1,len(node_table.columns)):
        # If the property contains numeric data, save the nodes with property values that are not NA and > 0
        if pd.api.types.is_numeric_dtype(node_table.iloc[:,node_property]):
            nodes_by_col.append(node_table.loc[node_table.iloc[:,node_property].notna() &
                                               node_table.iloc[:,node_property] > 0, 'NODEID'].tolist())
        # If the property contains boolean data, save the nodes with property values that are True
        else:
            nodes_by_col.append(node_table.loc[node_table.iloc[:,node_property] == True, 'NODEID'].tolist())

    # Initialize list to store network summary data
    nw_info = []
    
    # Iterate through each network file path
    for idx, file_path in enumerate(file_paths):
        # Load in the network
        nw = nx.read_edgelist(file_path)
        # Save the network name, number of nodes, number edges, and number of connected components
        nw_name = os.path.basename(file_path)
        number_nodes = nw.number_of_nodes()
        number_edges = nw.number_of_edges()
        ncc = nx.number_connected_components(nw)
        nw_info.append([nw_name,
                        number_nodes,
                        number_edges,
                        ncc])
        
        # Iterate through each node property and save the intersection with the current network
        for node_list in nodes_by_col:
            num_nodes = len([node for node in list(nw) if node in node_list])
            nw_info[idx].append(num_nodes)
    
    # Convert the network summary data to pandas dataframe
    nw_info = pd.DataFrame(nw_info, columns = ['name',
                                               'number of nodes',
                                               'number of edges',
                                               'number of connected components'] + nodes_by_col_labs)
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
