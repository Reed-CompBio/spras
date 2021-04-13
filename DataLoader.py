import pandas as pd
import warnings
import os

"""
Author: Chris Magnano
02/15/21

Methods and intermediate state for loading data and putting it into pandas tables for use by pathway reconstruction algorithms. We'll probably want to eventually roll these up as a part of another class.
"""

class DataLoader:

    NODE_ID = "NODEID"
    warning_threshold = 0.05 #Threshold for scarcity of columns to warn user

    def __init__(self, config):
        self.dataContext = None
        self.interactome = None
        self.nodeDatasets = None
        self.nodeTable = None
        self.edgeTable = None
        self.nodeSet = set()
        self.otherFiles = []
        self.loadFilesFromConfig(config)
        #TODO add ability to generically just grab all files
        return

    def loadFilesFromConfig(self, config):
        '''
        Loads data files from config, which is assumed to be a nested dictionary
        from a loaded yaml config file with the fields in Config-Files/config.yaml.
        Populates nodeDatasets, nodeTable, edgeTable, and interactome.

        nodeDatasets is a dictionary of pandas tables, while nodeTable is a single
        merged pandas table.

        When loading data files, files of only a single column with node
        identifiers are assumed to be a binary feature where all listed nodes are
        True.

        We might want to eventually add an additional "algs" argument so only
        subsets of the entire config file are loaded, alternatively this could
        be handled outside this class.

        returns: none
        '''

        #Get file paths from config
        interactomeLoc = config["reconstruction_settings"]["locations"]["interactome_path"]
        nodeDatasetFiles = config["data"]["datasets"]
        nodeDataFiles = config["data"]["otherNodeData"]
        edgeDataFiles = [""] #Currently None
        dataLoc = config["data"]["data_dir"]

        #Load everything as pandas tables
        self.interactome = pd.read_table(interactomeLoc, names = ["Interactor1","Interactor2","Weight"])
        nodeSet = set(self.interactome.Interactor1.unique())
        nodeSet = nodeSet.union(set(self.interactome.Interactor2.unique()))

        #Load node datasets
        self.nodeDatasets = dict()
        for dataset in nodeDatasetFiles:
            self.nodeDatasets[dataset] = pd.DataFrame(nodeSet, columns=[self.NODE_ID])
            for fileName in os.listdir(dataLoc):
                if fileName.startswith(dataset):
                    singleNodeTable = pd.read_table(os.path.join(dataLoc,fileName))
                    #If we have only 1 column, assume this is an indicator variable
                    if len(singleNodeTable.columns)==1:
                        singleNodeTable = pd.read_table(os.path.join(dataLoc,fileName),header=None)
                        singleNodeTable.columns = [self.NODE_ID]
                        #We assume there's a character splitting the dataset name and the rest of the file name
                        newColName = fileName[len(dataset)+1:].split(".")[0]
                        singleNodeTable[newColName] = True
                    self.nodeDatasets[dataset] = self.nodeDatasets[dataset].merge(singleNodeTable, how="left", on=self.NODE_ID, suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)")

        #Load generic node tables
        self.nodeTable = pd.DataFrame(nodeSet, columns=[self.NODE_ID])
        for nodeFile in nodeDataFiles:
            singleNodeTable = pd.read_table(os.path.join(dataLoc,nodeFile))
            #If we have only 1 column, assume this is an indicator variable
            if len(singleNodeTable.columns)==1:
                singleNodeTable = pd.read_table(os.path.join(dataLoc,nodeFile),header=None)
                singleNodeTable.columns = [self.NODE_ID]
                newColName = nodeFile.split(".")[0]
                singleNodeTable[newColName] = True

            self.nodeTable = self.nodeTable.merge(singleNodeTable, how="left", on=self.NODE_ID, suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)")
        self.otherFiles = config["data"]["otherFiles"]
        return

    def requestNodeColumns(self, colNames):
        '''
        returns: A table containing the requested column names and node ID's
        for all nodes with at least 1 of the requested values being non-empty
        '''
        dataNodeTable = self.nodeTable.merge(self.nodeDatasets[self.dataContext], how="left", on=self.NODE_ID, suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)" )
        for col in colNames:
            if col not in dataNodeTable:
                return None
        colNames.append(self.NODE_ID)
        filteredTable = dataNodeTable[colNames]
        filteredTable = filteredTable.dropna(axis=0, how='all',subset=filteredTable.columns.difference([self.NODE_ID]))
        percentHit = (float(len(filteredTable))/len(dataNodeTable))*100
        if percentHit <= self.warning_threshold*100:
            warnings.warn("Only %0.2f of data had one or more of the following columns filled:"%(percentHit) + str(colNames))
        return filteredTable

    def requestEdgeColumns(self, colNames):
        return None

    def getOtherFiles(self):
        return self.otherFiles.copy()

    def getInteractome(self):
        return self.interactome.copy()

    def set_data_context(self, dataset):
        self.dataContext = dataset
        return
