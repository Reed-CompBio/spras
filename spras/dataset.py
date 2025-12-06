import os
import pickle as pkl
import warnings
from typing import Union

import pandas as pd

from spras.config.dataset import DatasetSchema
from spras.util import FileLike, open_weak

"""
Author: Chris Magnano
02/15/21

Methods and intermediate state for loading data and putting it into pandas tables for use by pathway reconstruction algorithms.
"""

class Dataset:

    NODE_ID = "NODEID"
    warning_threshold = 0.05  # Threshold for scarcity of columns to warn user

    def to_file(self, file: FileLike):
        """Saves dataset object to pickle file"""
        with open_weak(file, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def from_file(cls, file: Union[FileLike, "Dataset"]):
        """
        Loads dataset object from a pickle file or another `Dataset` object.
        Usage: dataset = Dataset.from_file(pickle_file)
        """
        if isinstance(file, Dataset):
            # No work to be done (this use-case is used when processing
            # `Dataset` objects in generate_inputs or parse_outputs.)
            return file

        with open_weak(file, "rb") as file:
            return pkl.load(file)

    def __init__(self, dataset_params: DatasetSchema):
        """
        Loads data files from dataset_params, which is one dataset schema object
        from the list in the config file with the fields in the config file.
        Creates a new `Dataset` instance.

        node_table is a single merged pandas table.

        When loading data files, files of only a single column with node
        identifiers are assumed to be a binary feature where all listed nodes are
        True.

        We might want to eventually add an additional "algs" argument so only
        subsets of the entire config file are loaded, alternatively this could
        be handled outside this class.
        """

        self.label = dataset_params.label

        # Get file paths from config
        # TODO support multiple edge files
        interactome_loc = dataset_params.edge_files[0]
        node_data_files = dataset_params.node_files
        # edge_data_files = [""]  # Currently None
        data_loc = dataset_params.data_dir

        # Load everything as pandas tables
        self.interactome = pd.read_table(
            os.path.join(data_loc, interactome_loc), sep="\t", header=None
        )
        num_cols = self.interactome.shape[1]
        if num_cols == 3:
            self.interactome.columns = ["Interactor1", "Interactor2", "Weight"]
            # When no direction is specified, default to undirected edges
            self.interactome["Direction"] = "U"

        elif num_cols == 4:
            self.interactome.columns = [
                "Interactor1",
                "Interactor2",
                "Weight",
                "Direction",
            ]

            # Make directionality column case-insensitive
            self.interactome["Direction"] = self.interactome["Direction"].str.upper()
            if not self.interactome["Direction"].isin(["U", "D"]).all():
                raise ValueError(f"The Direction column for {self.label} edge file {interactome_loc} contains values "
                                 f"other than U and D")

        else:
            raise ValueError(
                f"Edge file {interactome_loc} must have three or four columns but found {num_cols}"
            )

        node_set = set(self.interactome.Interactor1.unique())
        node_set = node_set.union(set(self.interactome.Interactor2.unique()))

        # Load generic node tables
        self.node_table = pd.DataFrame(node_set, columns=[self.NODE_ID])
        for node_file in node_data_files:
            single_node_table = pd.read_table(os.path.join(data_loc, node_file))
            # If we have only 1 column, assume this is an indicator variable
            if len(single_node_table.columns) == 1:
                single_node_table = pd.read_table(
                    os.path.join(data_loc, node_file), header=None
                )
                single_node_table.columns = [self.NODE_ID]
                new_col_name = str(node_file).split(".")[0]
                single_node_table[new_col_name] = True

            # Use only keys from the existing node table so that nodes that are not in the interactome are ignored
            # If there duplicate columns, keep the existing column and add the suffix '_DROP' to the new column so it
            # will be ignored
            # TODO may want to warn about duplicate before removing them, for instance, if a user loads two files that
            #  both have prizes
            self.node_table = self.node_table.merge(
                single_node_table, how="left", on=self.NODE_ID, suffixes=(None, "_DROP")
            ).filter(regex="^(?!.*DROP)")
        # Ensure that the NODEID column always appears first, which is required for some downstream analyses
        self.node_table.insert(0, "NODEID", self.node_table.pop("NODEID"))
        self.other_files = dataset_params.other_files

    def get_node_columns(self, col_names: list[str]) -> pd.DataFrame:
        """
        returns: A table containing the requested column names and node IDs
        for all nodes with at least 1 of the requested values being non-empty
        """
        if self.node_table is None:
            raise ValueError("node_table is None: can't request node columns of an empty dataset.")

        col_names.append(self.NODE_ID)
        filtered_table = self.node_table[col_names]
        filtered_table = filtered_table.dropna(
            axis=0, how="all", subset=filtered_table.columns.difference([self.NODE_ID])
        )
        percent_hit = (float(len(filtered_table)) / len(self.node_table)) * 100
        if percent_hit <= self.warning_threshold * 100:
            # Only use stacklevel 1 because this is due to the data not the code context
            warnings.warn(
                "Only %0.2f of data had one or more of the following columns filled:"
                % (percent_hit)
                + str(col_names),
                stacklevel=1,
            )
        return filtered_table

    def contains_node_columns(self, col_names: list[str] | str):
        if self.node_table is None:
            raise ValueError("node_table is None: can't request node columns of an empty dataset.")
        """
        col_names: A list-like object of column names to check or a string of a single column name to check.
        returns: Whether or not all columns in col_names exist in the dataset.
        """
        if isinstance(col_names, str):
            return col_names in self.node_table.columns
        else:
            for c in col_names:
                if c not in self.node_table.columns:
                    return False
                return True

    def get_other_files(self):
        return self.other_files.copy()

    def get_interactome(self) -> pd.DataFrame | None:
        if self.interactome is None:
            raise ValueError("interactome is None: can't copy a non-existent interactome.")
        return self.interactome.copy(deep = True)
