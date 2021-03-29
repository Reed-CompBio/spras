#
# Tobias Rubel | rubelato@reed.edu
# CompBio
#
# This program generates precision and recall data for a given run of an algorithm
# when given a path of the form [algorithm]_[interactome]_[pathway]
# as well as ground truth data about the pathway in question in the form of
# ...
# It assumes that the directory structure for each named directory is as follows:
#
#   algorithm_interactome_pathway/
#   └── ranked-edges.csv
#
# where the ranked-edges.csv file should look as follows:
# #Tail, Head, k
# change documentation to say it works for many algorithms at once


import utils
import os
import sys
import random
import getopt
import time

import numpy as np
import pandas as pd

def load_df_tab(name:str):
    return pd.read_csv(name,sep='\t',engine='python')


def get_k(k: int,df: pd.DataFrame) -> pd.DataFrame:
    """
    :k       rank
    :df      dataframe of edges
    :returns sub-dataframe of k-ranked (or less) edges
    """
    return df[df['rank'] <= k][['#tail','head','pathway_name']]

def make_edges(df: pd.DataFrame) -> set:
    """
    :df      pandas dataframe
    :returns set of edge tuples
    """
    ## ignore edges incident to SRC or SINK
    return {frozenset(x) for x in df.values if x[0] != 'SRC' and x[1] != 'SNK'}

def make_nodes(df: pd.DataFrame) -> set:
    """
    :df      pandas dataframe
    :returns set of nodes
    """
    ## ignore nodes SRC or SINK
    n1 = {(x[0],x[2]) for x in df.values if x[0] != 'SRC'}
    n2 = {(x[1],x[2]) for x in df.values if x[1] != 'SNK'}
    return n1.union(n2)

def precision(prediction: set,truth:set,negs: set) -> float:
    prediction = {x for x in prediction if x in truth or x in negs}
    try:
        #print('  old precision: %d nodes in truth or negs; %d in truth' % (len(prediction),len(prediction.intersection(truth))))
        return len(prediction.intersection(truth))/(len(prediction))
    except:
        #an exception occurs just in case the prediction is neither in
        #the positive nor negative set. Thus we filter it out.
        return np.NaN

def recall(prediction: set,truth: set,negs: set) -> float:
    prediction = {x for x in prediction if x in truth or x in negs}
    return len(prediction.intersection(truth))/(len(truth))

def pr_nodes(predictions: pd.DataFrame,truth: set,negatives: set,pname:str,ranked=False,point=False,verbose=False,debug=False) -> dict:
    """
    :prediction dataframe of ranked edges
    :ground     dataframe of "ground truth" edges
    :returns    dictionary of precision keys to recall values
    """
    p = {} # dictionary of (recall, precision) pairs

    if verbose:
        print('first 10 nodes from pos:',list(truth)[:10])
    ## don't need to mess with negatives; they're alredady set.
    print('{} negative nodes ({} of {} total positives)'.format(len(negatives),len(negatives)/len(truth),len(truth)))
    if verbose:
        print('first 10 nodes from negs:',list(negatives)[:10])

    ## if it's ranked and not a point, compute PR for ranking.
    if ranked and not point:
        try:
            predictions = predictions.rename(columns={'KSP index':'rank'})
        except Exception as e:
            print('WARNING: predictions column is not "KSP index" or "rank"')
            print(e)

        ## make pred_dictionary of (node,best_rank) key/value pairs.
        ## here, keep the lowest rank of the nodes.
        pred_dict = {}
        for u,v,r,pname in predictions[['#tail','head','rank','pathway_name']].values:
            dict_key = (u,pname)
            if u != 'SRC' and (dict_key not in pred_dict or r < pred_dict[dict_key]):
                pred_dict[dict_key] = r
            dict_key = (v,pname)
            if v != 'SNK' and (dict_key not in pred_dict or r < pred_dict[dict_key]):
                pred_dict[dict_key] = r

        # make pred_list as (pred,rank) tuples
        # sort in place by increasing rank.
        pred_list = [(k,v) for k,v in pred_dict.items()]
        pred_list.sort(key = lambda x: x[1])
        if verbose:
            print('first 10 elements of pred_list are',pred_list[:10])
        p = pr_fast(pred_list,truth,negatives,verbose=verbose,debug=debug)

    else:
        # Either the method is unranked OR we're computing a single point.
        # In both of these cases, take the full set.
        prediction = make_nodes(predictions[['#tail','head','pathway_name']])
        p[recall(prediction,truth,negatives)] = precision(prediction,truth,negatives)

    # keep only nonzero (key,value) pairs
    p = {k:v for k,v in p.items() if (v != 0 and k != 0)}

    return p

def pr_fast(predictions:list,truth:set, negs:set, verbose=False,debug=False) -> dict:
    """
    :predictions: list of [pred,val] tuples, where pred is either frozenset(n,pathway) or frozenset(u,v,pathway).
    :truth: set of ground truth preds - either frozenset(n,pathway) or frozenset(u,v,pathway)
    :negs: set of negatives - either frozenset(n,pathway) or frozenset(u,v,pathway)
    """
    p = {} # dictionary of (rec,prec) values
    # note that this will keep the lowes (rec,prec) value if there are
    # multiple precisions at the same recall (e.g. we encounter a run of negs).

    counter,num_preds,num_TPs = 0,0,0
    prev_val,prev_rec,prev_prec = -1,-1,-1
    pred_set = set()
    for pred,val in predictions:

        if pred in pred_set:
            ## we've already evaluated this. Skip.
            ## for example it might be (u,v) when (v,u) has already been seen.
            continue

        pred_set.add(pred)
        counter+=1
        if pred in truth or pred in negs: # count if it's not ignored
            num_preds+=1
        if pred in truth: # count if it's a TP
            num_TPs+=1

         # continue if we've only seen ignored preds so far.
        if num_preds == 0:
            continue

        prec = num_TPs/num_preds
        rec = num_TPs/len(truth)

        ## at this point we have new rec,prec.
        ## If this is the FIRST of a value (e.g. we're in 2 in the list 1,1,1,1,2).
        ## add the previous rec,prec pair to the list to denote the previous
        ## (potentially tied) values.

        if val != prev_val and prev_rec != -1: # new value (not tied!) Add previous entry.
            if verbose:
                print('adding',prev_val,prev_prec,prev_rec)
            p[prev_rec] = prev_prec

        if verbose:# and counter % 100 == 0:
            print('processing prediction for value=%d (%d of %d): %d pos and %d negs encountered. prec %.2f and rec %.2f' % (val,counter,len(predictions),num_TPs,num_preds-num_TPs,prec,rec))
            print('  pred:',pred,'pred in truth:',pred in truth,'pred in negs:',pred in negs)

        if debug:
            old_prec = precision(pred_set,truth,negs)
            old_rec = recall(pred_set,truth,negs)
            if old_prec != prec or old_rec != rec:
                print('-'*10)
                print('processing prediction for value=%d (%d of %d): %d pos and %d negs encountered. prec %.2f and rec %.2f' % (val,counter,len(predictions),num_TPs,num_preds-num_TPs,prec,rec))
                print('  old prec %.2f and old rec %.2f' % (old_prec,old_rec))
                sys.exit('PREC/REC VALS ARE DIFFERENT! exiting.')

        # update the previous val to be this one.
        prev_val = val
        prev_prec = prec
        prev_rec = rec

    if num_preds > 0: ## add the last entry if it's been computed
        p[rec] = prec
    return p

def pr(dname: str,negative:set,truth:set,pname: str, point=False,ignore_adjacents=False) -> None:
    """
    :dname       algorithm_interactome_pathway
    :negatives   a set of negatives to use
    :returns     nothing
    :side-effect makes and saves precision-recall data for dname
    """
    #fetch prediction
    try:
        predictions = load_df_tab(os.path.join(dname,'ranked-edges.csv'))
        try: #fix headers if needed
            predictions = predictions.rename(columns={'tail':'#tail','#head':'head'})
        except:
            pass
    except:
        print('could not find ranked edges file for {}'.format(dname))
        return

    ranked = 'KSP index' in predictions.columns or 'rank' in predictions.columns

    start = time.time()
    p2 = pr_nodes(predictions,truth,negative,pname,ranked,point,verbose=True,debug=True)
    end = time.time()
    print('LOG NODES: %s\tpoint=%s\tranked=%s\ttime=%f' % (dname,point,ranked,end-start))
    try:
        p2 = [(k,v) for k, v in sorted(p2.items(), key=lambda item: item[0])]
        df = pd.DataFrame({'recall':[k for k,v in p2],'precision':[v for k,v in p2]})
        print(df)
        if ignore_adjacents:
            print('wrote to %s' % (os.path.join(dname,'pr-nodes-ignoreadj.csv')))
            df.to_csv(os.path.join(dname,'pr-nodes-ignoreadj.csv'),index=False)
        else:
            print('wrote to %s' % (os.path.join(dname,'pr-nodes.csv')))
            df.to_csv(os.path.join(dname,'pr-nodes.csv'),index=False)
    except Exception as e:
        print(e)

    nf = pd.DataFrame({'negatives':sorted(list(negative))})
    if ignore_adjacents:
        print('wrote to %s' % (os.path.join(dname,'negatives-nodes-ignoreadj.csv')))
        nf.to_csv(os.path.join(dname,'negatives-nodes-ignoreadj.csv'),index=False)
    else:
        print('wrote to %s' % (os.path.join(dname,'negatives-nodes.csv')))
        nf.to_csv(os.path.join(dname,'negatives-nodes.csv'),index=False)

def get_negatives(interactome: pd.DataFrame,positives: set,pname,num:int=0,bivalent=False) -> set:
    """
    :interactome dataframe of interaction data
    :num         number of negatives to randomly generate
    :positives   set of positives
    :returns     k probable negatives
    """
    if num == 0:
        num = len(positives)*50
    edges = make_edges(interactome.take([0,1],axis=1))
    edges = {tuple(e) for e in edges}
    #nodes = set()
    #for e in edges:
#        nodes.update(set(e))
    nodes = set([e[0] for e in edges]).union(set([e[1] for e in edges]))
    print('%d total nodes (%.3f are positives)' % (len(nodes),len(positives)/len(nodes)))
    nodes = nodes - positives
    print('%d total'% (len(nodes)))
    if bivalent:
        return nodes

    samp = set(random.sample(list(nodes),k=num))
    psamp = {(a,pname) for a in samp}
    return psamp

def main(argv: str) -> None:
    """
    :args        first argument should be path where the directories reside
                 the other arguments should be directories as per the format
                 requirements at the top of this document
    :returns     nothing
    :side-effect makes precision recall if possible
    """
    try:
        path,IGNORE_ADJ,directories = argv[1],eval(argv[2]),argv[3:]
        print(path)
        print('ignore adjacents?',IGNORE_ADJ)
        print('generating precision recall data for the following: {}'.format(directories))
    except:
        print('arguments are required...')
        return
    try:
        os.chdir(path)
    except:
        print("path either doesn't exist or could not be accessed.")
    #fetch pathway name
    pname = directories[0].split('_')[-2]
    interactome = load_df_tab(os.path.join(directories[0],'interactome.csv'))
    ground = load_df_tab(os.path.join(directories[0],'ground.csv'))
    truth = make_nodes(ground[['#tail','head','pathway_name']])

    ## get negatives.
    #fname = os.path.join(directories[0],'negatives-nodes.csv')
    #if os.path.isfile(fname):
    #    with open(os.path.join(directories[0],'negatives-nodes.csv'),'r') as f:
    #        negative = {eval(eval(x)) for x in f.read().splitlines()[1:]}
    #else:
    negative = get_negatives(interactome,truth,pname)
    print('%d negatives and %d positives' % (len(negative),len(truth)))
    if IGNORE_ADJ:
        print('IGNORING ADJACENT NEGS....')
        edges = make_edges(interactome.take([0,1],axis=1))
        edges = {tuple(e) for e in edges}
        to_remove_1 = {(e[0],pname) for e in edges if (e[0],pname) not in truth and (e[1],pname) in truth}
        to_remove_2 = {(e[1],pname) for e in edges if (e[1],pname) not in truth and (e[0],pname) in truth}
        negative_ignoreadj = negative - to_remove_1 - to_remove_2
        print('--> removing %d edge-adjacent positives'  %(len(negative)-len(negative_ignoreadj)))
        print('--> %d negatives_ignoreadj\n' % (len(negative_ignoreadj)))

    for d in directories:
        print('\n'+'='*10,'Running',d,'='*10)
        try:
            p = os.path.join(d,'config.conf')
            print('config file:',p)
            conf = pd.read_csv(os.path.join(d,'config.conf'),sep=' = ',engine='python')
        except Exception as e:
            print('no conf file for {}'.format(d))
            print(e)
            return e
        POINT = conf[conf['value'] == 'POINT']['bool'].bool()
        if IGNORE_ADJ:
            pr(d,negative_ignoreadj,truth,pname,POINT,ignore_adjacents=IGNORE_ADJ)
        else:
            pr(d,negative,truth,pname,POINT,ignore_adjacents=IGNORE_ADJ)

if __name__ == '__main__':
    main(sys.argv)
