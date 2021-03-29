import sys
import networkx as nx
import json


#wrapper functions for nx methods here 

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


def load_graph(path: str) -> nx.Graph:
    try:
        G = nx.read_edgelist(path)
    except:
        print('file format not yet supported. submit a feature request if it ought to be!')
    return G

def save(data,pth):
    with open(pth,'w') as f:
        json.dump(data,f)


def main(argv):
    G = load_graph(argv[1])
    print(G.nodes)
    dat = produce_statistics(G)
    print(dat)
    save(dat,argv[2])


if __name__ == "__main__":
    main(sys.argv)

