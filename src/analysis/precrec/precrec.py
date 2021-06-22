import sys
import random
import os
import numpy as np
import pandas as pd
import Dataset

# Modified from PRAUG's Precision-Recall code.
def compute_precrec(infiles:list,data:Dataset, gt_header:str, outprefix:str,subsample:str) -> None:
    print(infiles)
    print(data)
    print(gt_header)
    print(outprefix)
    print(subsample)
    print('???'*20)
    if data.contains_node_columns([gt_header]):
        ## items are NODES
        predictions,positives,negatives = get_node_items(infiles,data,gt_header)

    elif data.contains_edge_columns([gt_header]):
        ## items are UNDIRECTED EDGES
        sys.exit('NOT IMPLEMENTED')
    else:
        sys.exit('Error: %s not in nodes or edges of dataset.'%gt_header)

    # subsample negatives.
    try:
        sub_num = float(subsample)
        print('Subsampling to be %f times as many negatives as posiives.' % (sub_num))
        ## TODO ended here.
    except:
        assert subsample=='all'
        print('using all negatives.')
    # TODO this could be only run if negatives file doesn't exist.
    # For now, always subsample to be sure we are plotting against the same items.

    # for every pred, compute prec-rec, write to file, and store coords.

    # plot coords.
    return

def get_node_items(infiles,data,gt_header):
    ## get all items
    all_items = set(data.node_table[data.NODE_ID])

    ## get positives
    pos = set(data.request_node_columns([gt_header])[data.NODE_ID])

    ## get negatives
    neg = all_items.difference(pos)

    ## check that num negs + num pos = num all items.
    assert len(pos)+len(neg)==len(all_items)

    ## get predictions
    preds = {}
    for f in infiles:
        t = pd.read_table(f, delim_whitespace=True,names = ["u","v","rank"])

        # make a table of ranked nodes
        u_table = t[["u","rank"]]
        v_table = t[["v","rank"]]
        v_table.columns=["u","rank"]
        node_t = u_table.append(v_table,ignore_index=True)

        # collapse table, keeping minimum value for each node.
        print('BEFORE COLLAPSING')
        print(node_t.loc[node_t['u']=="Q15750"])
        #https://stackoverflow.com/questions/12497402/python-pandas-remove-duplicates-by-columns-a-keeping-the-row-with-the-highest
        node_t = node_t.sort_values("rank",ascending=True).drop_duplicates("u").sort_index()
        #print(node_t)
        print('AFTER COLLAPSING')
        print(node_t.loc[node_t['u']=="Q15750"])

        preds[f] = node_t

    return preds,pos,neg

def get_edge_items(infiles,data,gt_header):

    return
