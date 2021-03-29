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
        print('  old precision: %d nodes in truth or negs; %d in truth' % (len(prediction),len(prediction.intersection(truth))))
        return len(prediction.intersection(truth))/(len(prediction))
    except:
        #an exception occurs just in case the prediction is neither in
        #the positive nor negative set. Thus we filter it out.
        return np.NaN

def recall(prediction: set,truth: set,negs: set) -> float:
    prediction = {x for x in prediction if x in truth or x in negs}
    return len(prediction.intersection(truth))/(len(truth))

def pr_edges(predictions: pd.DataFrame,ground: pd.DataFrame,negatives: set,pname:str,ranked=False,point=False,verbose=False,debug=False) -> dict:
    """
    :prediction dataframe of ranked edges
    :ground     dataframe of "ground truth" edges
    :returns    dictionary of precision keys to recall values
    :note: this whole routine needs to be rewritten
    """
    p = {} # dictionary of (recall, precision) pairs

    #turn ground truth into set of edges
    truth = make_edges(ground[['#tail','head','pathway_name']])
    #check to see if this is a ranked method
    print('  {} NEGATIVE EDGES ({}X of {} total positives)'.format(len(negatives),len(negatives)/len(truth),len(truth)))

    #print('pr edges ranked = {}'.format(ranked))
    ## if it's ranked and not a point, compute PR for ranking.
    if ranked and not point:
        try:
            predictions = predictions.rename(columns={'KSP index':'rank'})
        except Exception as e:
            print('WARNING: predictions column is not "KSP index" or "rank"')
            print(e)

        # make pred_list as (pred,rank) tuples
        # sort in place by increasing rank.
        pred_list = [(frozenset((x[0],x[1],x[3])),x[2]) for x in predictions[['#tail','head','rank','pathway_name']].values if x[0] != 'SRC' and x[1] != 'SNK']
        pred_list.sort(key = lambda x: x[1])
        if verbose:
            print('first 10 elements of pred_list are',pred_list[:10])
        p = pr_fast(pred_list,truth,negatives,verbose=verbose,debug=debug)

    else:
        # Either the method is unranked OR we're computing a single point.
        # In both of these cases, take the full set.
        prediction = make_edges(predictions[['#tail','head','pathway_name']])
        p[recall(prediction,truth,negatives)] = precision(prediction,truth,negatives)

    # keep only nonzero (key,value) pairs
    p = {k:v for k,v in p.items() if (v != 0 and k != 0)}

    return p

def pr_nodes(predictions: pd.DataFrame,ground: pd.DataFrame,edge_negatives: set,pname:str,ranked=False,point=False,verbose=False,debug=False) -> dict:
    """
    :prediction dataframe of ranked edges
    :ground     dataframe of "ground truth" edges
    :returns    dictionary of precision keys to recall values
    """
    p = {} # dictionary of (recall, precision) pairs

    #turn ground truth into set of nodes
    truth = make_nodes(ground[['#tail','head','pathway_name']])
    #print('first 10 nodes from truth:',list(truth)[:10])

    ## convert edge negatives to node negatives
    ## To handle frozensets, first get all negative nodes.
    #negatives = {(y,x[3]) for x in negatives for y in x[:2]}
    negatives = set()
    for n in edge_negatives:
        negatives.update(set(n))
    try:
        negatives.remove(pname)
    except:
        pass
    ## then stitch the negatives back together.
    negatives = {(x,pname) for x in negatives}
    print('  {} NEGATIVE NODES ({}X of {} total positives)'.format(len(negatives),len(negatives)/len(truth),len(truth)))
    #print('first 10 nodes from negs:',list(negatives)[:10])

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

        if debug:
            old_prec = precision(pred_set,truth,negs)
            old_rec = recall(pred_set,truth,negs)
            if old_prec != prec or old_rec != rec:
                print('  old prec %.2f and old rec %.2f' % (old_prec,old_rec))
                sys.exit()

        # update the previous val to be this one.
        prev_val = val
        prev_prec = prec
        prev_rec = rec

    if num_preds > 0: ## add the last entry if it's been computed
        p[rec] = prec
    return p

def pr(dname: str,negative:set,pname: str, edges=True,point=False) -> None:
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
    #fetch ground truth
    try:
        ground = load_df_tab(os.path.join(dname,'ground.csv'))
    except:
        print('could not find ground truth for {}'.format(dname))
        return
    #load interactome and generate negatives
    try:
        interactome = load_df_tab(os.path.join(dname,'interactome.csv'))
    except:
        print('could not find interactome for {}'.format(dname))
        return

    ranked = 'KSP index' in predictions.columns or 'rank' in predictions.columns

    if edges == True or edges == '#': ## RUN EDGES
        print('\nRunning Edge PR')
        start = time.time()
        p1 = pr_edges(predictions,ground,negative,pname,ranked,point)
        end = time.time()
        print('LOG EDGES: %s\tpoint=%s\tranked=%s\ttime=%f' % (dname,point,ranked,end-start))
        try:
            p1 = [(k,v) for k, v in sorted(p1.items(), key=lambda item: item[0])]
            df = pd.DataFrame({'recall':[k for k,v in p1],'precision':[v for k,v in p1]})
            print(df)
            df.to_csv(os.path.join(dname,'pr-edges.csv'),index=False)
            print('wrote to %s' % (os.path.join(dname,'pr-edges.csv')))
        except Exception as e:
            print(e)

    if edges == False or edges == '#': ## RUN NODES
        print('\nRunning Node PR')
        start = time.time()
        p2 = pr_nodes(predictions,ground,negative,pname,ranked,point)
        end = time.time()
        print('LOG NODES: %s\tpoint=%s\tranked=%s\ttime=%f' % (dname,point,ranked,end-start))
        try:
            p2 = [(k,v) for k, v in sorted(p2.items(), key=lambda item: item[0])]
            df = pd.DataFrame({'recall':[k for k,v in p2],'precision':[v for k,v in p2]})
            df.to_csv(os.path.join(dname,'pr-nodes.csv'),index=False)
            print('wrote to %s' % (os.path.join(dname,'pr-nodes.csv')))
        except Exception as e:
            print(e)

    nf = pd.DataFrame({'negatives':list(negative)})
    nf.to_csv(os.path.join(dname,'negatives.csv'),index=False)

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
    edges = edges - positives
    if bivalent:
        return edges
    samp = set(random.sample(list(edges),k=num))
    psamp = {frozenset((a,b,pname)) for (a,b) in samp}
    ## Nnode negs should be determined here too. - AR
    return psamp

def pull_negatives(pname: str,ndir: str) -> set:
    """
    :pname   pathway name
    :ndir    negatives directory
    :returns negative set
    """
    print(os.listdir(ndir))
    print(pname)
    nset = next(x for x in os.listdir(ndir) if pname in x)
    with open(os.path.join(ndir,nset),'r') as f:
        return {eval(eval(x)) for x in f.read().splitlines()[1:]}


def main(argv: str) -> None:
    """
    :args        first argument should be path where the directories reside
                 the other arguments should be directories as per the format
                 requirements at the top of this document
    :returns     nothing
    :side-effect makes precision recall if possible
    """
    try:
        path,directories = argv[1],argv[2:]
        print('generating precision recall data for the following: {}'.format(directories))
    except:
        print('arguments are required...')
        return
    directories = [os.path.join(path,d) for d in directories]

    #try:
    #    os.chdir(path)
    #except:
    #    print("path either doesn't exist or could not be accessed.")
    #fetch pathway name
    print(directories[0])
    pname = directories[0].split('/')[-1].split('_')[2]
    print(pname)
    #path to hardcoded negatives
    prefix = '/'.join(argv[0].split('/')[:-1])
    #negpath = '{}/negatives'.format(prefix)
    negpath = os.path.join(prefix,'negatives')
    print('NEGPATH:',negpath)
    interactome = load_df_tab(os.path.join(directories[0],'interactome.csv'))
    ground = load_df_tab(os.path.join(directories[0],'ground.csv'))
    FIXED_NEGATIVES = False
    if FIXED_NEGATIVES == False:
        negative = get_negatives(interactome,make_edges(ground.take([0,1],axis=1)),pname)
    else:
        negative = pull_negatives(pname,negpath)
    print('%d negatives' % (len(negative)))
    for d in directories:
        try:
            p = os.path.join(d,'config.conf')
            print(p)
            conf = pd.read_csv(os.path.join(d,'config.conf'),sep=' = ',engine='python')
        except Exception as e:
            print('no conf file for {}'.format(d))
            print(e)
            return e
        POINT = conf[conf['value'] == 'POINT']['bool'].bool()
        pr(d,negative,pname,'#',POINT)
        



if __name__ == '__main__':
    main(sys.argv)
