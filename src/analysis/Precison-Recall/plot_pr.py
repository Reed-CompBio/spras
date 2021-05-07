#
# Tobias Rubel | rubelato@reed.edu
# CompBio
#
# This program creates precision recall plots given a path followed by a save path,
# followed by a list of directory names to plot from.
#
# It assumes that the names are as follows: [algorithm]_[interactome]_[pathway]
# It assumes that the directory structure for each named directory is as follows:
#
#   algorithm_interactome_pathway/
#   ├── negatives.csv
#   └── pr.csv
import re
import sys
import os
import utils
from itertools import cycle
import pandas as pd
import matplotlib.pyplot as plt

## GLOBAL DICTIONARIES
MARKERS = {'BTB':'o',
    'PCSF':'v',
    'RN':'^',
    'SP':'<',
    }
COLORS = {'BTB':'r','PRAUG-BTB':'r',
    'PCSF':'g','PRAUG-PCSF':'g',
    'PL':'b','PRAUG-PL':'b','PRAUG-PL-BFS':'r','PRAUG-PL-WEIGHTED':'c','PRAUG-PL-BFS-WEIGHTED':'m',
    'RN':'c','PRAUG-RN':'c',
    'RWR':'m','PRAUG-RWR':'m','PRAUG-RWR-BFS':'b','PRAUG-RWR-WEIGHTED':'r','PRAUG-RWR-BFS-WEIGHTED':'c',
    'SP':'#D09F0E','PRAUG-SP':'#D09F0E',
    'PRAUG-GT-NODES':'k',
    'PRAUG-GT-EDGES':'#8D5D27',
    }

PARAM_COLORS = {'PRAUG-PL_2018_Wnt_k50':'#D5D8DC',
'PRAUG-PL_2018_Wnt_k100':'#ABB2B9',
'PRAUG-PL_2018_Wnt_k500':'#808B96',
'PRAUG-PL_2018_Wnt_k1000':'#566573',
'PRAUG-PL_2018_Wnt_k5000':'#1C2833',
'PL_2018_Wnt_k5000':'b',
'PRAUG-RWR_2018_Wnt_a0.85-t0.1':'#EAECEE',
'PRAUG-RWR_2018_Wnt_a0.85-t0.2':'#D5D8DC',
'PRAUG-RWR_2018_Wnt_a0.85-t0.3':'#ABB2B9',
'PRAUG-RWR_2018_Wnt_a0.85-t0.4':'#808B96',
'PRAUG-RWR_2018_Wnt_a0.85-t0.5':'#566573',
'PRAUG-RWR_2018_Wnt_a0.85-t0.75':'#1C2833',
'RWR_2018_Wnt_a0.85-t0.75':'m',
}

PARAM_NAMES = {'PRAUG-PL_2018_Wnt_k50':'PRAUG-PL $k=50$',
'PRAUG-PL_2018_Wnt_k100':'PRAUG-PL $k=100$',
'PRAUG-PL_2018_Wnt_k500':'PRAUG-PL $k=500$',
'PRAUG-PL_2018_Wnt_k1000':'PRAUG-PL $k=1000$',
'PRAUG-PL_2018_Wnt_k5000':'PRAUG-PL $k=5000$',
'PL_2018_Wnt_k5000':'PL $k=5000$',
'PRAUG-RWR_2018_Wnt_a0.85-t0.1':'PRAUG-RWR $\\tau=0.1$',
'PRAUG-RWR_2018_Wnt_a0.85-t0.2':'PRAUG-RWR $\\tau=0.2$',
'PRAUG-RWR_2018_Wnt_a0.85-t0.3':'PRAUG-RWR $\\tau=0.3$',
'PRAUG-RWR_2018_Wnt_a0.85-t0.4':'PRAUG-RWR $\\tau=0.4$',
'PRAUG-RWR_2018_Wnt_a0.85-t0.5':'PRAUG-RWR $\\tau=0.5$',
'PRAUG-RWR_2018_Wnt_a0.85-t0.75':'PRAUG-RWR $\\tau=0.75$',
'RWR_2018_Wnt_a0.85-t0.75':'RWR $\\tau=0.75$'
}

COMPLETE_LIST = ['BTB', 'PCSF', 'PL', 'RN', 'RWR', 'SP', 'PRAUG-GT-EDGES', 'PRAUG-GT-NODES']

# routines to verify that it makes sense to compare the precision and recall of
# the different algorithms by ensuring that they were computed on the same
# interactome, that they were predicting the same pathway, and that they used
# the same negatives.

def verify_negatives(lat: list,node_motivation=False,composite=False,verbose=False) -> bool:
    """
    :lat     list of directory names
    :returns True iff the runs were made with the same negatives
    """
    if node_motivation: ## skip this for now if node_motivation is specified.
        negfilenames = ['negatives-nodes.csv','negatives-nodes-ignoreadj.csv']
    elif composite:
        return True
    else:
        negfilenames = ['negatives.csv']

    toReturn = {}
    for negfilename in negfilenames:
        #get one of the lists of negatives as a dataframe
        df = utils.read_df(lat[0],negfilename)

        if verbose:
            for j in lat[1:]:
                print(os.path.join(j,negfilename),df.equals(utils.read_df(j,negfilename)))
        #exploiting transitivity of identity, compare the first against all others
        toReturn[negfilename] = all(df.equals(i) for i in [utils.read_df(j,negfilename) for j in lat[1:]])
    return all(list(toReturn.values()))

def verify_pathway(lat: list) -> bool:
    """
    :lat     list of directory names
    :returns True iff the runs were made on the same pathway
    """
    #helper function which gives us the pathway name given a formatted filename
    f = lambda x: x.split('_')[2]
    #get one of the pathways
    p = f(lat[0])
    #exploiting transitivity of identity, compare the first against all others
    return all(p == q for q in [f(l) for l in lat[1:]])

def verify_interactome(lat: list) -> bool:
    """
    :lat     list of directory names
    :returns True iff the runs were made on the same interactome
    """
    #helper function which gives us the pathway name given a formatted filename
    f = lambda x: x.split('_')[1]
    #get one of the pathways
    p = f(lat[0])
    #exploiting transitivity of identity, compare the first against all others
    return all(p == q for q in [f(l) for l in lat[1:]])

def verify_coherence(lat: list,node_motivation=False,composite=False) -> bool:
    """
    :lat     list of directory names
    :returns True iff all of the coherence checks pass
    """
    return all([verify_negatives(lat,node_motivation,composite),verify_pathway(lat),verify_interactome(lat)])

# routines that handle the plotting of the precision recall plots

def pr(name: str,edges=True,ignore_adj=False) -> (list,list):
    """
    :name    name of directory
    :edges   (trivalent) boolean as to whether we are plotting edges,nodes or both
    :returns recall, precision
    """
    #fetch precision and recall
    if edges == True:
        df = utils.read_df(name,'pr-edges.csv')
    elif edges == False:
        if ignore_adj == True:
            df = utils.read_df(name,'pr-nodes-ignoreadj.csv')
        else:
            df = utils.read_df(name,'pr-nodes.csv')
    df = df.sort_values(by=['recall','precision'],ascending=[True,False])
    #df = df.sort_values('precision',ascending=False)
    recall = list(df['recall'])
    precision = list(df['precision'])
    return recall,precision


def plot(lat: list, spath: str,params=False,edges=True,full_axis=True) -> None:
    """
    :lat         list of directory names
    :spath       name of save path
    :edges       (trivalent) boolean as to whether we are plotting edges,nodes or both
    :returns     nothing
    :side-effect saves a plot to spath
    """
    #initialize pyplot figure
    max_recall = -1
    min_precision = 2
    if (edges == True or edges == False):
        #fig = plt.figure()
        fig = plt.figure(figsize=(4,4)) # used for benchmark figs
        ax = fig.add_subplot(111)
        #plot each precision recall plot
        for l in sorted(lat,key=lambda t:len(t)):
            print(l)
            #get algorithm name for legend
            #lname = '-'.join([l.split('_')[0],l.split('_')[-1]])
            if params:
                lname = l.split('/')[-1]
                color_dict = PARAM_COLORS
            else:
                lname = l.split('/')[-1].split('_')[0]
                color_dict = COLORS
            #plot
            recall,precision=pr(l,edges)
            max_recall = max(max_recall,max(recall))
            min_precision = min(min_precision,min(precision))
            if 'PRAUG' in lname or params:
                alpha_val = 0.9
                lw=4
            else:
                alpha_val = 0.3
                lw=2
            if len(recall)==1:

                ax.plot(recall,precision,label=lname,color=color_dict[lname],marker=MARKERS[lname_orig],ms=10,alpha=alpha_val,zorder=2)
            else:
                ax.plot(recall,precision,label=PARAM_NAMES.get(lname,lname),color=color_dict[lname],lw=lw,alpha=alpha_val,zorder=1)
    elif edges == '#':
        fig = plt.figure(figsize=(12,5))
        ax = fig.add_subplot(121)
        #plot each precision recall plot
        for l in lat:
            #get algorithm name for legend
            lname = l.split('_')[0]
            #plot
            ax.plot(*pr(l,True),label=lname,marker=next(markers),alpha=0.7)
        cax = fig.add_subplot(122)
        #plot each precision recall plot
        for l in lat:
            #get algorithm name for legend
            if params:
                lname = l.split('/')[-1]
            else:
                lname = l.split('/')[-1].split('_')[0]
            #plot
            cax.plot(*pr(l,False),label="_nolegend_",marker=next(markers),alpha=0.7)
    #format figure globally
    #ax.legend()
    handles, labels = ax.get_legend_handles_labels()
    # sort both labels and handles by labels. There has to be a better way to do this but this hosuld work.
    new_labels = []
    new_handles = []
    seen = set()
    for l in COMPLETE_LIST:
        for i in range(len(labels)):
            if l in labels[i] and labels[i] not in seen:
                new_labels.append(labels[i])
                new_handles.append(handles[i])
                seen.add(labels[i])

    if params:
        ax.legend(new_handles, new_labels)
    else:
        ax.legend(new_handles, new_labels)#,ncol=2,loc='lower right')
    title = lat[0].split('/')[-1].split('_')[2] + ' Pathway'
    #fig.suptitle(title,fontsize=16)
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title(title + ' Interactions')
    ax.grid(linestyle='--')
    if full_axis or max_recall == -1:
        ax.set_xlim(0,1)
        ax.set_ylim(0,1.02)
    else:
        print(min_precision,max_recall)
        ax.set_xlim(0,min(max_recall+0.15,1.0))
        ax.set_ylim(max(min_precision-0.1,0),1.02)
    if edges == '#':
        cax.set_xlabel('Recall')
        cax.set_ylabel('Precision')
        cax.set_title(title + ' Proteins')
        cax.grid(linestyle='--')
        cax.set_xlim(0,1)
        cax.set_ylim(0,1)

    #save the plot
    print(lat)
    lat = [x.replace('HybridLinker','HL') for x in lat]
    lat = [x.replace('PerfectLinker','PeL') for x in lat]

    methods = [x.split('/')[-1].split('_') for x in lat]
    infix = [m[0] for m in methods]+methods[0][1:]
    if edges:
        sname = 'edges-'+'-'.join(infix)+'.png'
    else:
        sname = 'nodes-'+'-'.join(infix)+'.png'

    #in order to incorporate the save path
    #some more work needs to be done.
    plt.tight_layout()
    #plt.subplots_adjust(left=0.21)
    #plt.subplots_adjust(top=0.90)
    print(spath,sname)
    plt.savefig(os.path.join(spath,sname))

    sname = sname.replace('.png','.pdf')
    plt.savefig(os.path.join(spath,sname))
    os.system('pdfcrop %s %s' % (os.path.join(spath,sname),os.path.join(spath,sname)))
    print('writing to %s'% (os.path.join(spath,sname)))

def fmax(csvdoc: str) -> float:
   df = pd.read_csv(csvdoc)
   vs = [tuple(x) for x in df.values]
   f1 = lambda p,r:2*((p*r)/(p+r))
   return max([f1(*v) for v in vs])


def plot_composite(lat: list, spath: str,) -> None:
    """
    :lat         list of directory names
    :spath       name of save path
    :edges       (trivalent) boolean as to whether we are plotting edges,nodes or both
    :returns     nothing
    :side-effect saves a plot to spath
    """
    #initialize pyplot figure
    markers = iter(['o','v','^','<','>','p','*','h','H','+','x','X','D','d','|','_'][:len(lat)]*50)
    fig, axs = plt.subplots(2, 3,figsize=(25,15))
    plotloc = axs.flat
    print(axs)
    #turn list of methods into list of tuples of things to plot together:
    combine_key = {'PRAUG-BTB':'BTB','PRAUG-SP':'SP','PRAUG-PL':'PL','PRAUG-RN':'RN','PRAUG-PCSF':'PCSF','PRAUG-RWR':'RWR'}
    partner = lambda x: next(y for y in lat if re.match('^{}_'.format(combine_key[x]),y))
    old_lat = lat
    p = lat[0].split('/')[0]
    lat = [x.split('/')[-1] for x in lat]
    lat = [(x,partner(x.split('_')[0])) for x in lat if x.split('_')[0] in combine_key]
    lat = [tuple([os.path.join(p,x) for x in l]) for l in lat]
    print(lat)
    #plot each precision recall plot
    for l in lat:
        loc = next(plotloc)
        print(loc)
        #get algorithm name for legend
        #plot
        print(l[0])
        f0 = fmax(os.path.join(l[0],'pr-edges.csv'))
        l1name = l[0].split('/')[-1].split('_')[0]+' fmax = {}'.format(f0)
        f1 = fmax(os.path.join(l[1],'pr-edges.csv'))
        loc.plot(*pr(l[0],True),label=l1name,marker=next(markers),markersize=10,color='deepskyblue',alpha=1.0)
        #get algorithm name for legend (once more with feeling!)
        l2name = l[1].split('/')[-1].split('_')[0]+' fmax = {}'.format(f1)
        #plot
        loc.plot(*pr(l[1],True),label=l2name,marker=next(markers),markersize=10,color='blueviolet',alpha=1.0)
        """
        loc = next(plotloc)
        print(loc)
        #get algorithm name for legend
        l1name = l[0].split('_')[0]
        #plot
        loc.plot(*pr(l[0],True),label=l1name,marker=next(markers),alpha=0.7)
        #get algorithm name for legend (once more with feeling!)
        l2name = l[1].split('_')[0]
        #plot
        loc.plot(*pr(l[1],True),label=l2name,marker=next(markers),alpha=0.7)
        """
    #format figure globally
    title = 'Composite Interaction Performance across 29 Pathways'
    fig.suptitle(title,fontsize=16)
    plt.xticks(fontsize=14)
    for ax in axs.flat:
        ax.set_xlabel('Recall',fontsize=14)
        ax.set_ylabel('Precision',fontsize=14)
        ax.grid(linestyle='--')
        ax.legend(loc='top right')
    #toggle axes
    plt.setp(axs, xlim=(0,1), ylim=(0,1))
    #save the plot
    old_lat = [x.replace('HybridLinker','HL') for x in old_lat]
    old_lat = [x.replace('PerfectLinker','PeL') for x in old_lat]
    sname = 'full-composite.pdf'
    #in order to incorporate the save path
    #some more work needs to be done.
    plt.tight_layout()
    #plt.subplots_adjust(left=0.21)
    plt.subplots_adjust(top=0.90)
    plt.savefig(os.path.join(spath,sname))

def plot_node_motivation(lat: list, spath: str) -> None:
    """
    :lat         list of directory names
    :spath       name of save path
    :edges       (trivalent) boolean as to whether we are plotting edges,nodes or both
    :returns     nothing
    :side-effect saves a plot to spath
    """
    #initialize pyplot figure
    markers = iter(['o','v','^','<','>','1','2','3','4','8','s','p','P','*','h','H','+','x','X','D','d','|','_'][:len(lat)]*50)
    fig = plt.figure()
    ax = fig.add_subplot(111)

    color_cycle = cycle(['r','g','b', 'c', 'm', '#D09F0E', 'k'])
    #plot each precision recall plot
    for l in lat:
        #get algorithm name for legend
        lname = l.split('/')[-1].split('_')[0]
        #plot
        this_color = COLORS[lname]
        recall,precision = pr(l,False,False)
        recall2,precision2 = pr(l,False,True)
        if len(recall) == 1:
            this_marker = MARKERS[lname]
            ax.plot(recall,precision,this_marker,color=this_color,label=lname,marker=this_marker,ms=10,alpha=0.3,zorder=2)
            ax.plot(recall2,precision2,this_marker,color=this_color,label=lname +'$^*$',marker=this_marker,ms=10,alpha=0.9,zorder=2)
            ax.plot([recall[0],recall2[0]],[precision[0],precision2[0]],'--',color=this_color,alpha=0.3,zorder=2)
        else:
            ax.plot(recall,precision,color=this_color,label=lname,lw=4,alpha=0.3,zorder=1)
            ax.plot(recall2,precision2,color=this_color,label=lname +'$^*$',lw=4,alpha=0.9,zorder=1)
            ax.plot([recall[0],recall2[0]],[precision[0],precision2[0]],'--',color=this_color,alpha=0.3,zorder=1)
            ax.plot([recall[-1],recall2[-1]],[precision[-1],precision2[-1]],'--',color=this_color,alpha=0.3,zorder=1)

    #format figure globally
    #ax.legend()

    title = ' '.join(lat[0].split('_')[1:])

    ax.set_xlabel('Node Recall')
    ax.set_ylabel('Node Precision')
    ax.set_title('Reconstructing Wnt Proteins',fontsize=14)
    ax.set_ylim(0,1.02)
    ax.set_xlim(0,1.02)

    methods = [x.split('/')[-1].split('_') for x in lat]
    infix = [m[0] for m in methods]+methods[0][1:]
    sname = 'node-motivation-' + '-'.join(infix)+'.png'

    #in order to incorporate the save path
    #some more work needs to be done.
    #plt.plot([], [], ' ', label="*No edge-adjacent\nnegatives")
    plt.legend(loc='lower left',ncol=2,fontsize=12)
    plt.tight_layout()
    #plt.subplots_adjust(left=0.21)
    #plt.subplots_adjust(top=0.90)
    plt.savefig(os.path.join(spath,sname))
    print('writing to %s'% (os.path.join(spath,sname)))
    sname = sname.replace('.png','.pdf')
    plt.savefig(os.path.join(spath,sname))
    os.system('pdfcrop %s %s' % (os.path.join(spath,sname),os.path.join(spath,sname)))
    print('writing to %s'% (os.path.join(spath,sname)))

#handle input
def main(args: list) -> None:
    """
    :args        first argument should be path where the directories reside
                 the other arguments should be directories as per the format
                 requirements at the top of this document
    :returns     nothing
    :side-effect plots precision recall if possible
    """
    #get current directory to pass through to plot
    #cdir = os.getcwd()
    #change to working directory
    try:
        path,spath,directories = args[1],args[2],sorted(list(set(args[3:])))
        print('plotting the following: {}'.format(directories))
    except:
        print('arguments are required...')
    directories = [os.path.join(path,d) for d in directories]
    #try:
    #    os.chdir(path)
    #except:
    #    print("path {} either doesn't exist or could not be accessed.".format(path))

    ## these are HARD-CODED - need to make them arguments.
    COMPOSITE=False
    NODE_MOTIVATION=False
    PARAMS=False
    FULL_AXIS = True
    if verify_coherence(directories,NODE_MOTIVATION,COMPOSITE):
        if COMPOSITE:
            plot_composite(directories,spath)
        elif NODE_MOTIVATION:
            plot_node_motivation(directories,spath)
        else: # plot regular PR
            plot(directories,spath,PARAMS,True,FULL_AXIS)
        return


    else:
        print('Coherence could not be established. Terminating...')
        print('\nVerifying Negatives:')
        print(verify_negatives(directories,NODE_MOTIVATION,True))
        print('\nVerifying Pathway:')
        print(verify_pathway(directories))
        print('\nVerifying Interactome:')
        print(verify_interactome(directories))






if __name__ == '__main__':
    main(sys.argv)
