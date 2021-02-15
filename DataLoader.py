import pandas as pd

"""
Author: Chris Magnano
02/15/21

Methods and intermediate state for loading data and putting it into pandas tables for use by pathway reconstruction algorithms. We'll probably want to eventually roll these up as a part of another class.
"""

NODE_ID = "Uniprot"

class DataLoader:

    def __init__(self, config):
        self.interactome = None
        self.nodeDatasets = None
        self.nodeTable = None
        self.edgeTable = None
        self.nodeSet = set()
        self.otherFiles = []
        self.loadFilesFromConfig(config)
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

        #Load everything as pandas tables
        self.interactome = pd.read_table(interactomeLoc, names = ["Interactor1","Interactor2","Weight"])
        nodeSet = set(self.interactome.Interactor1.unique())
        nodeSet = nodeSet.union(set(self.interactome.Interactor2.unique()))

        #Load node datasets
        self.nodeDatasets = dict()
        for dataset in nodeDataFiles:
            self.nodeDatasets[dataset] = pd.read_table(dataset)

        #Load generic node tables
        self.nodeTable = pd.DataFrame(nodeSet, columns=[NODE_ID])
        for nodeFile in nodeDataFiles:
            singleNodeTable = pd.read_table(nodeFile)
            #If we have only 1 column, assume this is an indicator variable
            if len(singleNodeTable.columns)==1:
                newColName = singleNodeTable.columns[0]
                singleNodeTable.rename(columns={newColName: NODE_ID})
                singleNodeTable[newColName] = True

            #TODO: Validate this is the kind of join we want, check column names
            #Currently basing on this: https://stackoverflow.com/questions/19125091/pandas-merge-how-to-avoid-duplicating-columns
            self.nodeTable = self.nodeTable.merge(singleNodeTable, how="left", on=NODE_ID, suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)")
            #TODO: This counts row misses, add a warning message
            percentHit = len(singleNodeTable)/float(self.nodeTable)

        self.otherFiles = config["data"]["otherFiles"]



        return

    def requestNodeColumns(self, colNames):
        '''
        returns: A table containing the requested column names and node ID's
        for all nodes with at least 1 of the requested values being non-empty
        '''
        filteredTable = self.nodeTable.dropna(axis=0, how='all')
        colNames.append(NODE_ID)
        newTable = filteredTable[colNames]
        return

    def requestNodeDataset(self, datasetName):
        '''
        returns: A copy of the requested dataset
        '''
        return self.nodeDatasets[datasetName].copy()

    def requestEdgeColumns(self, colNames):
        return None

    def getOtherFiles(self):
        return self.otherFiles.copy()
