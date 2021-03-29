#
# Tobias Rubel | rubelato@reed.edu
# Reed CompBio
#
# This program generates a plot illustrating the variance of a method (or methods)
# with respect to changes in negative sets.
import re
import utils
import sys
import os
import shutil
import subprocess
import pandas as pd
import matplotlib.pyplot as plt
from sklearn import metrics
from scipy import integrate
from statistics import median

def init(d:str,dest: str,c=25) -> None:
    """
    :d    name of directory to copy
    :dest destination directory for copied data
    :c    number of copies to make
    """
    try:
        os.mkdir(dest)
    except:
        try:
            os.remove(os.path.join(dest,'{}-AUCs.csv'.format(d)))
        except:
            pass
    for i in range(c):
        try:
            shutil.copytree(d,os.path.join(dest,'{}-{}'.format(i,d.split('/')[-1])))
        except:
            pass


def re_PR(dest):
    for x in os.listdir(dest):
        CALL = 'python3 make_pr.py {} {}'.format(dest,x)
        subprocess.call(CALL.split())

def load_pr(path: str,fname: str) -> pd.DataFrame:
    """
    :path    to csv
    :fname   of csv
    :returns DataFrame of precision,recall
    """
    return pd.read_csv(os.path.join(path,fname))

def AUC(df: pd.DataFrame) -> float:
    """
    :df      DataFrame of precision,recall
    :returns definite integral of df at max recall 
    """
    #sort the dataframe
    df = df.sort_values(by=['recall','precision'],ascending=[True,False])
    return metrics.auc(df['recall'],df['precision'])
    #return integrate.simps(df['precision'],df['recall'])


def find_median(dest,e=True):
    #compute AUC for all and return the integer id of
    #the plot closest to the median for plotting
    d = dict()
    for rn in os.listdir(dest):
        if 'AUC' in rn:
            pass
        elif e == True:
            df = load_pr(os.path.join(dest,rn),'pr-edges.csv')
            d[rn.split('-')[0]] = AUC(df)
        elif e == False:
            df = load_pr(os.path.join(dest,rn),'pr-nodes.csv')
            d[rn.split('-')[0]] = AUC(df)
    with open(os.path.join(dest,'{}-AUCs.csv'.format(dest)),'w') as f:
        for x in d.values():
            f.write('{}\n'.format(x))
    print(d)
    return next(k for k in d if d[k] == median(d.values()))

def pr(name: str,edges=True) -> (list,list):
    """
    :name    name of directory
    :edges   (trivalent) boolean as to whether we are plotting edges,nodes or both
    :returns recall, precision
    """
    #fetch precision and recall
    if edges == True:
        df = utils.read_df(name,'pr-edges.csv')
    elif edges == False:
        df = utils.read_df(name,'pr-nodes.csv')
    df = df.sort_values(by=['recall','precision'],ascending=[True,False])
    #df = df.sort_values('precision',ascending=False)
    recall = list(df['recall'])
    precision = list(df['precision'])
    return recall,precision


def plot(dpath: str, spath: str,med,edges=True) -> None:
    """
    :dpath       location with all runs
    :spath       name of save path
    :med         median run
    :edges       (trivalent) boolean as to whether we are plotting edges,nodes or both
    :returns     nothing
    :side-effect saves a plot to spath
    """
    lat = [os.path.join(dpath,x) for x in os.listdir(dpath) if not 'AUC' in x]
    #initialize pyplot figure
    markers = iter(['o','v','^','<','>','1','2','3','4','8','s','p','P','*','h','H','+','x','X','D','d','|','_'][:len(lat)]*50)
    if (edges == True or edges == False):
        fig = plt.figure()
        ax = fig.add_subplot(111)
        #resort lat such that med is the last thing plotted
        medl = next(x for x in lat if '{}-'.format(med) in x)
        print(medl)
        lat.remove(medl)
        lat.append(medl)
        #plot each precision recall plot
        for l in lat:
            #get algorithm name for legend
            lname = l.split('_')[0]
            #plot
            if l == medl:
                print('med')
                ax.plot(*pr(l,edges),label=lname,marker='o',alpha=1.0,color='royalblue')
            else:
                print('not med')
                ax.plot(*pr(l,edges),label=lname,marker='o',alpha=0.3,color='cornflowerblue')
    #format figure globally
    #ax.legend()
    #fig.legend(loc='center left')
    title = ' '.join(lat[0].split('_')[1:])
    fig.suptitle(title,fontsize=16)
    ax.set_xlabel('Recall')
    ax.set_ylabel('Precision')
    ax.set_title('Interactions')
    ax.grid(linestyle='--')
    #save the plot
    #lat = [x.replace('HybridLinker','HL') for x in lat]
    #lat = [x.replace('PerfectLinker','PeL') for x in lat]
    sname = 'vartest.png'
    #in order to incorporate the save path 
    #some more work needs to be done.
    plt.tight_layout()
    #plt.subplots_adjust(left=0.21)
    plt.subplots_adjust(top=0.90)
    plt.savefig(os.path.join(spath,sname))



def main(argv):
    d = argv[1]
    dest = argv[2]
    c = int(argv[3])
    print('initializing directory')
    init(d,dest,c)
    print('computing PR')
    re_PR(dest)
    print('computing median auc')
    med = find_median(dest)
    print(med)
    print('plotting')
    plot(dest,'plots',med)


if __name__ == "__main__":
    main(sys.argv)

    
