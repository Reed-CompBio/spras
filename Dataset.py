import pandas as pd
import numpy as np
import warnings
import os
import pickle as pkl

"""
Author: Chris Magnano
02/15/21

Methods and intermediate state for loading data and putting it into pandas tables for use by pathway reconstruction algorithms.
"""

class Dataset:

    NODE_ID = "NODEID"
    EDGE_ID_A = "NODEAID"
    EDGE_ID_B = "NODEBID"
    warning_threshold = 0.05 #Threshold for scarcity of columns to warn user

    def __init__(self, dataset_dict):
        self.label = None
        self.interactome = None
        self.node_table = None
        self.edge_table = None
        self.node_set = set()
        self.other_files = []
        self.load_files_from_dict(dataset_dict)
        return

    def to_file(self, file_name):
        '''
        Saves dataset object to pickle file
        '''
        with open(file_name, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def from_file(cls, file_name):
        '''
        Loads dataset object from a pickle file.
        Usage: dataset = Dataset.from_file(pickle_file)
        '''
        with open(file_name, "rb") as f:
            return pkl.load(f)

    def load_files_from_dict(self, dataset_dict):
        '''
        Loads data files from dataset_dict, which is one dataset dictionary from the list
        in the config file with the fields in the config file.
        Populates node_table, edge_table, and interactome.

        node_table is a single merged pandas table.

        When loading data files, files of only a single column with node
        identifiers are assumed to be a binary feature where all listed nodes are
        True.

        We might want to eventually add an additional "algs" argument so only
        subsets of the entire config file are loaded, alternatively this could
        be handled outside this class.

        returns: none
        '''

        self.label = dataset_dict["label"]

        #Get file paths from config
        # TODO support multiple edge files
        interactome_loc = dataset_dict["edge_files"][0]
        node_data_files = dataset_dict["node_files"]
        edge_data_files = [""] #Currently None
        ground_truth_files = dataset_dict["ground_truth_files"]
        data_loc = dataset_dict["data_dir"]

        #Load everything as pandas tables
        self.interactome = pd.read_table(os.path.join(data_loc,interactome_loc), names = ["Interactor1","Interactor2","Weight"])
        node_set = set(self.interactome.Interactor1.unique())
        node_set = node_set.union(set(self.interactome.Interactor2.unique()))

        # Load generic edge table as UNDIRECTED.
        self.edge_table = self.interactome[["Interactor1","Interactor2"]]
        self.edge_table.columns= [self.EDGE_ID_A,self.EDGE_ID_B]
        self.edge_table = self.make_edges_undirected(self.edge_table)

        #Load generic node tables
        self.node_table = pd.DataFrame(node_set, columns=[self.NODE_ID])
        for node_file in node_data_files:
            single_node_table = pd.read_table(os.path.join(data_loc,node_file))
            #If we have only 1 column, assume this is an indicator variable
            if len(single_node_table.columns)==1:
                single_node_table = pd.read_table(os.path.join(data_loc,node_file),header=None)
                single_node_table.columns = [self.NODE_ID]
                new_col_name = node_file.split(".")[0]
                single_node_table[new_col_name] = True

            self.node_table = self.node_table.merge(single_node_table, how="left", on=self.NODE_ID, suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)")

        # Load ground truth tables.
        for gt_file in ground_truth_files:
            single_gt_table = pd.read_table(os.path.join(data_loc,gt_file),header=None)
            #If we have only one column, assume it is a NODES list.
            #print(gt_file,len(single_gt_table.columns))
            if len(single_gt_table.columns)==1:
                single_gt_table.columns = [self.NODE_ID]
                new_col_name = gt_file.split(".")[0]
                single_gt_table[new_col_name] = True

                self.node_table = self.node_table.merge(single_gt_table, how="left", on=self.NODE_ID, suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)")

            # If we have two columns, assume it is an EDGES list.
            elif len(single_gt_table.columns)==2:
                single_gt_table.columns=[self.EDGE_ID_A,self.EDGE_ID_B]
                single_gt_table = self.make_edges_undirected(single_gt_table)

                new_col_name = gt_file.split(".")[0]
                single_gt_table[new_col_name] = True

                self.edge_table = self.edge_table.merge(single_gt_table, how="left", on=[self.EDGE_ID_A,self.EDGE_ID_B], suffixes=("", "_DROP")).filter(regex="^(?!.*DROP)")

        # set other files
        self.other_files = dataset_dict["other_files"]

    def make_edges_undirected(self, table):
        # sort edges (e.g., directed edges u,v and v,u will become undirected u,v).
        # this seems slow, but I can't find another way to do this. - AR
        for index in table.index:
            table.loc[index] = sorted(list(table.iloc[[index]].values[0]))

        # drop duplicates
        table.drop_duplicates(inplace=True,ignore_index=True)
        return table

    def request_node_columns(self, col_names):
        '''
        returns: A table containing the requested column names and node IDs
        for all nodes with at least 1 of the requested values being non-empty
        '''
        col_names.append(self.NODE_ID)
        filtered_table = self.node_table[col_names]
        filtered_table = filtered_table.dropna(axis=0, how='all',subset=filtered_table.columns.difference([self.NODE_ID]))
        percent_hit = (float(len(filtered_table))/len(self.node_table))*100
        if percent_hit <= self.warning_threshold*100:
            warnings.warn("Only %0.2f of data had one or more of the following columns filled:"%(percent_hit) + str(col_names))
        return filtered_table

    def contains_node_columns(self, col_names):
        '''
        col_names: A list-like object of column names to check or a string of a single column name to check.
        returns: Whether or not all columns in col_names exist in the dataset.
        '''
        if isinstance(col_names, str):
            return col_names in self.node_table.columns
        else:
            for c in col_names:
                if c not in self.node_table.columns:
                    return False
                return True

    def request_edge_columns(self, col_names):
        '''
        returns: A table containing the requested column names and node IDs
        for all nodes with at least 1 of the requested values being non-empty
        '''
        col_names.append(self.NODE_ID_A)
        col_names.append(self.NODE_ID_B)
        filtered_table = self.edge_table[col_names]
        filtered_table = filtered_table.dropna(axis=0, how='all',subset=filtered_table.columns.difference([self.NODE_ID_A,self.NODE_ID_B]))
        percent_hit = (float(len(filtered_table))/len(self.edge_table))*100
        if percent_hit <= self.warning_threshold*100:
            warnings.warn("Only %0.2f of data had one or more of the following columns filled:"%(percent_hit) + str(col_names))
        return filtered_table

    def contains_edge_columns(self, col_names):
        '''
        col_names: A list-like object of column names to check or a string of a single column name to check.
        returns: Whether or not all columns in col_names exist in the dataset.
        '''
        if isinstance(col_names, str):
            return col_names in self.edge_table.columns
        else:
            for c in col_names:
                if c not in self.edge_table.columns:
                    return False
                return True

    def get_other_files(self):
        return self.other_files.copy()

    def get_interactome(self):
        return self.interactome.copy()
