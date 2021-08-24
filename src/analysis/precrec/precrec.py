import sys
import random
import os
import numpy as np
import pandas as pd
import Dataset
import matplotlib.pyplot as plt

# Modified from PRAUG's Precision-Recall code.
def compute_precrec(infiles:list, outfiles:list, data:Dataset, gt_header:str, outprefix:str,subsample:str) -> None:
    print(infiles)
    print(data)
    print(gt_header)
    print(outprefix)
    print(subsample)
    print('???'*20)
    if data.contains_node_columns([gt_header]):
        ## items are NODES
        predictions,positives,all_negatives = get_node_items(infiles,outfiles,data,gt_header)
    elif data.contains_edge_columns([gt_header]):
        ## items are UNDIRECTED EDGES
        sys.exit('NOT IMPLEMENTED')
    else:
        sys.exit('Error: %s not in nodes or edges of dataset.'%gt_header)

    # subsample negatives.
    try:
        sub_num = float(subsample)
        neg_size = int(sub_num*len(positives))
        if neg_size < len(all_negatives):
            print('Subsampling to be %f times as many negatives as positives = %d negatives' % (sub_num,neg_size))

            # TODO this could be only run if negatives file doesn't exist.
            # For now, always subsample to be sure we are plotting against the same items.
            negatives = random.sample(all_negatives,k=neg_size)
        else:
            print('WARNING: using all %d possible negatives.' % (len(all_negatives)))
            negatives = all_negatives
    except:
        assert subsample=='all'
        print('using all %d negatives.' % (len(all_negatives)))
        negatives = all_negatives

    # for every pred, compute prec-rec, write to file, and store coords.
    dfs = {} # dict of {outf: DataFrame} key-value pairs
    for outf,pred in predictions.items():
        dfs[outf] = pr(pred,positives,negatives,outf)
    print('%d data frames' % (len(dfs)))

    ## TODO we currently make output files AND plot the prec-rec values as PNGs.
    ## Make this an option in the config file that reads the output files from above
    ## to make this more snakemake-friendly...
    plot_pr(dfs,outprefix)

    print('DONE')
    return

def pr(pred:pd.DataFrame,pos:set,negs:set,outfile:str) -> pd.DataFrame:

    ## NOTE: the output file INCLUDES ALL PREDICTIONS, including those
    ## that are in the ignored set (neither a pos nor a neg)
    out = open(outfile,'w')
    out.write('#pred\trank\tTP\tFP\tprecision\trecall\n')

    # the fastest way to do this is one sweep, adding to
    # precision & recall when necessary. There are cleaner ways to do this
    # but they end up calculating prec & rec for larger and larger subsets
    # of the data...
    vals = [] # valls will be 2-col list of unique [prec,rec] vals.
    counter,num_preds,num_TPs = 0,0,0
    prev_rank,prev_prec,prev_rec,prec,rec = -1,-1,-1,-1,-1
    ties = []
    for index,row in pred.iterrows():
        u = row['u']
        rank = row['rank']
        if u in pos or u in negs: # count if it's not ignored
            num_preds+=1

        if u in pos: # count if it's a TP
            num_TPs+=1

        tp = '1' if u in pos else '0'
        fp = '1' if u in negs else '0'

        prec = num_TPs/num_preds
        rec = num_TPs/len(pos)

        if prev_rank != -1 and rank != prev_rank:
            # write all previous ties
            for line in ties:
                out.write('%s\t%.4f\t%.4f\n' % (line,prev_prec,prev_rec))
            ties = []
            # if this is a unique (prec,rec) combo, add it to vals.
            if prec != prev_prec and rec != prev_rec:
                vals.append([prec,rec])

        #print([u,str(rank),tp,fp,'%.4f'%(prec),'%.4f'%(rec)])
        ## add the prefix line to ties list.
        ties.append('\t'.join([u,str(rank),tp,fp]))

        # update previous PR values.
        prev_rank = rank
        prev_prec = prec
        prev_rec = rec

    # add last point if different from second-to-last.
    # catches the case where there are ties in the last rank.
    for line in ties:
        out.write('%s\t%.4f\t%.4f\n' % (line,prev_prec,prev_rec))
        # if this is a unique (prec,rec) combo, add it to vals.
        if len(vals)==0 or vals[-1] != [prec,rec]:
            vals.append([prec,rec])

    print('wrote to %s' % (outfile))
    out.close()

    # turn vals into a 2-column data frame.
    df = pd.DataFrame.from_records(vals,columns=['prec','rec'])
    print(df)
    return df

def plot_pr(dfs:dict,outprefix:str) -> None:
    fig = plt.figure()
    for outf in dfs:
        if len(dfs[outf]['rec'])>1: #plot line
            plt.plot(dfs[outf]['rec'],dfs[outf]['prec'],label=outf.split('/')[-1])
        else: # plot point
            plt.plot(dfs[outf]['rec'],dfs[outf]['prec'],'o',ms=5,label=outf.split('/')[-1])
    plt.xlim([0,1])
    plt.ylim([0,1])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(outprefix.split('/')[-1])
    plt.legend(loc='best')
    plt.tight_layout()
    plt.savefig(outprefix+'.png')
    print('Wrote to %s.png' % (outprefix))
    return


def get_node_items(infiles,outfiles,data,gt_header):
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
    for i in range(len(infiles)):
        f = infiles[i]
        fout = outfiles[i]
        t = pd.read_table(f, delim_whitespace=True,names = ["u","v","rank"])

        # make a table of ranked nodes
        u_table = t[["u","rank"]]
        v_table = t[["v","rank"]]
        v_table.columns=["u","rank"]
        node_t = u_table.append(v_table,ignore_index=True)

        # collapse table, keeping minimum value for each node.
        #print('BEFORE COLLAPSING')
        #print(node_t.loc[node_t['u']=="Q15750"])
        #https://stackoverflow.com/questions/12497402/python-pandas-remove-duplicates-by-columns-a-keeping-the-row-with-the-highest
        node_t = node_t.sort_values("rank",ascending=True).drop_duplicates("u")
        #print(node_t)
        #print('AFTER COLLAPSING')
        #print(node_t.loc[node_t['u']=="Q15750"])

        preds[fout] = node_t

    return preds,pos,neg

def get_edge_items(infiles,data,gt_header):

    return
