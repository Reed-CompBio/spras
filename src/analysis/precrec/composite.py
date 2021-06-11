#
# Tobias Rubel | rubelato@reed.edu
# Reed CompBio
#
# This program generates composite predictions
# run with -h for more info.


import os
import re
import pandas as pd
import shutil
import argparse
import sys



#DATA_PATH = 'refactor-test-data'
DATA_PATH = '/Volumes/compbio/2020-05-PRAUG/runs'

NEG_PATH = 'negatives'

def sanity_check(A:str,pathways: list) -> bool:
    """
    :A       name of algorithm
    :returns whether data exists for A for all pathways
    """
    global DATA_PATH
    dirs = [x for x in os.listdir(DATA_PATH) if A in x]
    for P in pathways:
        print(P)
        if not any(P in d for d in dirs):
            return False
    return True


def join(A: str,PATHWAYS,kargs) -> pd.DataFrame:
    global DATA_PATH
    dirs = [x for x in os.listdir(DATA_PATH) if re.match("^{}_.*_{}$".format(A,kargs[A]),x) and not 'composit' in x and any(P in x for P in PATHWAYS)]
    print(A)
    print(dirs)
    ## need to preserve args.
    print('*'*50)
    edge_lists = [os.path.join(DATA_PATH,os.path.join(d,'ranked-edges.csv')) for d in dirs]
    df = pd.read_csv(edge_lists[0],sep='\t')
    for d in edge_lists[1:]:
        df = pd.concat([df,pd.read_csv(d,sep='\t')])
    #for ranked edgelists...
    ranked = 'KSP index' in df.columns or 'rank' in df.columns
    if ranked:
        try:
            df = df.rename(columns={'KSP index':'rank'})
            #print(df)
        except Exception as e:
            print('*'*50)
            print(e)
            #print(df)
            pass
        df = df.sort_values(by='rank')
        df = df.drop_duplicates().reset_index(drop=True)
    return df

def join_pathways(PLAT: list) -> pd.DataFrame:
    print(PLAT)
    pathways = [os.path.join('../../Pathways','{}-edges.txt'.format(P)) for P in PLAT]
    df = pd.read_csv(pathways[0],sep='\t')
    for d in pathways[1:]:
        df = pd.concat([df,pd.read_csv(d,sep='\t')])
    df = df.drop_duplicates().reset_index(drop=True)
    return df


# argument parser
def parse_args(ALL_PATHWAYS,ALL_METHODS):
    parser = argparse.ArgumentParser()

    #add optional arguments
    parser.add_argument("-p","--pathways",metavar='STR',nargs="+",help="A list of pathways to make predictions for. Possible options are 'all' or:\n{}".format("\n".join(ALL_PATHWAYS)))
    parser.add_argument("-m","--methods",metavar='STR',nargs="+",help="A list of pathway reconstruction algorithms to run. Possible options are 'all' or:\n{}".format("\n".join(ALL_METHODS)))
    parser.add_argument("-i","--interactome",type=str,default='2018',help="The year of interactome. Possible options are '2015' and '2018'. Defaults to '2018'.")

    group = parser.add_argument_group('Pathway Reconstruction Method Arguments')
    group.add_argument('-k',type=int,metavar='INT',default=500,help="PathLinker: number of shortest paths (k). Default 500.")
    group.add_argument('-y',type=int,metavar='INT',default=20,help="ResponseNet: sparsity parameter (gamma). Default 20.")
    group.add_argument('-r',type=int,metavar='INT',default=5,help="PCSF: terminal prize (rho). Default 5.")
    group.add_argument('-b',type=int,metavar='INT',default=1,help="PCSF: edge reliability (b). Default 1.")
    group.add_argument('-w',type=int,metavar='INT',default=5,help="PCSF: dummy edge weight (omega). Default 5.")
    group.add_argument('-g',type=int,metavar='INT',default=3,help="PCSF: degree penalty (g). Default 3.")
    group.add_argument('-a',type=float,metavar='FLOAT',default=0.85,help="RWR: teleportation probability (alpha). Default 0.85.")
    group.add_argument('-t',type=float,metavar='FLOAT',default=0.5,help="RWR: flux threshold (tau). Default 0.5.")


    args = parser.parse_args()
    ## check that at least one pathway is specified.
    if args.pathways == None and not args.node_pr:
        parser.print_help()
        sys.exit('\nERROR: At least one pathway (-p) must be specified. Exiting.')
    elif args.pathways == ['all']:
        PATHWAYS = ALL_PATHWAYS
    else:
        PATHWAYS = args.pathways
        if any([p not in ALL_PATHWAYS for p in PATHWAYS]):
            sys.exit('\nERROR: Pathways can be "all" or from {}'.format(ALL_PATHWAYS))
    #patch out problem pathways FIX THIS !!
    #PATHWAYS.remove('ID')
    #PATHWAYS.remove('IL')
    #PATHWAYS.remove('IL9')
    #PATHWAYS.remove('RAGE')
    ## check that at least one method is specified
    if args.methods == None and not args.node_pr:
        parser.print_help()
        sys.exit('\nERROR: At least one method (-m) must be specified. Exiting.')
    elif args.methods == ['all']:
        METHODS = ALL_METHODS
    else:
        METHODS = args.methods
        if any([m not in ALL_METHODS for m in METHODS]):
            sys.exit('\nERROR: Methods can be "all" or from {}'.format(ALL_METHODS))
    return PATHWAYS, METHODS, args

def main(argv):
    #global PATHWAYS, DPATH, ALGORITHMS, INTERACTOME
    global DATA_PATH,NEG_PATH
    INTERACTOMES = {
    '2018':'../../Interactomes/PathLinker_2018_human-ppi-weighted-cap0_75.txt',
    '2015':'../../Interactomes/background-interactome-pathlinker-2015.txt'
    }

    ## PATHWAYS directory includes allNPnodes.txt and NP_pathways.zip; make sure that '-' is in the variable.
    ALL_PATHWAYS = {x.split('_')[2] for x in os.listdir(DATA_PATH) if len(x.split('_'))>=3 and not 'composite' in x}
    #ALL_PATHWAYS.discard('Oncostatin')
    #ALL_PATHWAYS.add('Oncostatin_M')
    #ALL_PATHWAYS.discard('TGF')
    #ALL_PATHWAYS.add('TGF_beta_Receptor')
    ALL_METHODS = {x.split('_')[0] for x in os.listdir(DATA_PATH) if len(x.split('_'))>=3 }

    ## parse arguments
    PATHWAYS,ALGORITHMS,args = parse_args(ALL_PATHWAYS,ALL_METHODS)
    INTERACTOME = args.interactome
    #perform sanity check to ensure that for all algorithms we have all data
    unsafe_algorithms = []
    for ALG in ALGORITHMS:
        if sanity_check(ALG,PATHWAYS):
            pass
        else:
            unsafe_algorithms.append(ALG)
    if len(unsafe_algorithms) != 0:
        print('the following algorithms are unsafe: {}.\nPlease ensure that data exists for all algorithms.'.format(', '.join(unsafe_algorithms)))
        print('proceeding anyway though?')
        #return
    #use kwargs for each method to get formatted strings for naming
    kargs = {'PCSF':'r{}-b{}-w{}-g{}'.format(args.r,args.b,args.w,args.g),'PRAUG-PCSF':'r{}-b{}-w{}-g{}'.format(args.r,args.b,args.w,args.g),
              'RWR':'a{}-t{}'.format(args.a,args.t),'PRAUG-RWR':'a{}-t{}'.format(args.a,args.t),
              'BTB':'','PRAUG-BTB':'',
               'SP':'','PRAUG-SP':'',
               'RN':'y{}'.format(args.y),'PRAUG-RN':'y{}'.format(args.y),
               'PL':'k{}'.format(args.k),'PRAUG-PL':'k{}'.format(args.k)}
    #make composit pathway
    composit_pathway = join_pathways(PATHWAYS)
    #make empty directories
    ddict = dict()
    for ALG in ALGORITHMS:
        if kargs[ALG] != '':
            name = '_'.join([ALG,INTERACTOME,'composite',kargs[ALG]])
        else:
            name = '_'.join([ALG,INTERACTOME,'composite'])
        DEST = os.path.join(DATA_PATH,name)
        ddict[ALG] = DEST
        try:
            os.mkdir(DEST)
        except:
            print('directory already existed. Not overwriting.')
    #populate directories with union predictions
    for ALG in ALGORITHMS:
        #os.remove(os.path.join(ddict[ALG],'*'))
        join(ALG,PATHWAYS,kargs).to_csv(os.path.join(ddict[ALG],'ranked-edges.csv'),sep='\t',index=False)
        composit_pathway.to_csv(os.path.join(ddict[ALG],'ground.csv'),sep='\t',index=False)
        interactome = os.path.abspath(INTERACTOMES[INTERACTOME]) ## to avoid relative path errors
        with open(os.path.join(ddict[ALG],'.pathway_log'),'w') as f:
                for x in PATHWAYS:
                    f.write('{}\n'.format(x))

        if not os.path.isfile(os.path.join(DEST,'interactome.csv')):
            if not os.path.isfile(interactome):
                sys.exit("ERROR: interactome doesn't exist:",interactome)
            try:
                os.remove(os.path.join(ddict[ALG],'interactome.csv'))
            except:
                pass
            os.symlink(interactome,os.path.join(ddict[ALG],'interactome.csv'))
        shutil.copy('config.conf',os.path.join(ddict[ALG],'config.conf'))
        print('Wrote files to {}'.format(ddict[ALG]))







if __name__ == "__main__":
    main(sys.argv)
