import os
import pickle as pkl
import warnings

import pandas as pd

class Evaluation:
   
    def __init__(self, gold_standard_dict):
        self.label = None
        self.node_table = None
        # self.edge_table = None TODO: later iteration
        self.load_files_from_dict(gold_standard_dict)
        return
    
    def to_file(self, file_name):
        """
        Saves dataset object to pickle file
        """
        with open(file_name, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def from_file(cls, file_name):
        """
        Loads dataset object from a pickle file.
        Usage: dataset = Dataset.from_file(pickle_file)
        """
        with open(file_name, "rb") as f:
            return pkl.load(f)

    def load_files_from_dict(self, gold_standard_dict):
         
        self.label = gold_standard_dict["label"]
        node_data_files = gold_standard_dict["node_files"]
        data_loc = gold_standard_dict["data_dir"]

        single_node_table = pd.read_table(os.path.join(data_loc, node_file))
        self.node_table = single_node_table


def percision_recall():
    None
    # https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html

def 