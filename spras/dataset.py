import copy
import os
import pickle as pkl
import warnings
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from enum import EnumMeta, StrEnum
from os import PathLike
from typing import Hashable, Optional, Self

import pandas as pd

from spras.interactome import (
    convert_directed_to_undirected,
    convert_undirected_to_directed,
)

"""
Author: Chris Magnano
02/15/21

Methods and intermediate state for loading data and putting it into pandas tables for use by pathway reconstruction algorithms.
"""

class Interactome:
    """
    Newtype validator over pd.DataFrame for input interactomes.
    """

    def __init__(self, interactome: pd.DataFrame):
        self.df = interactome
        num_cols = self.df.shape[1]
        if num_cols == 3:
            self.df.columns = ["Interactor1", "Interactor2", "Weight"]
            # When no direction is specified, default to undirected edges
            self.df["Direction"] = "U"

        elif num_cols == 4:
            self.df.columns = [
                "Interactor1",
                "Interactor2",
                "Weight",
                "Direction",
            ]

            # Make directionality column case-insensitive
            self.df["Direction"] = self.df["Direction"].str.upper()
            if not self.df["Direction"].isin(["U", "D"]).all():
                raise ValueError("The Direction column contains values other than U and D")

        else:
            raise ValueError("Interactome must have three or four columns but found {num_cols}")

    def get_nodes(self) -> set[str]:
        node_set = set(self.df.Interactor1.unique())
        node_set = node_set.union(set(self.df.Interactor2.unique()))
        return node_set

    @classmethod
    def from_file(cls, file: str | PathLike):
        return cls(pd.read_table(file, sep="\t", header=None))

    def __copy__(self):
        return Interactome(self.df.copy(deep=False))

    def __deepcopy__(self, memo):
        return Interactome(self.df.copy(deep=True))


# https://stackoverflow.com/a/63804868/7589775
class ABCEnumMeta(EnumMeta, ABCMeta):
    pass

class InteractomeProperty(StrEnum, metaclass=ABCEnumMeta):
    """
    If a class extends this, then that means it acts as a property of the interactome.
    One could get, validate, or guarantee that an interactome has this property.
    """

    @staticmethod
    def priority() -> int:
        """
        The priority of an interactome property, used in `guarantee_interactome`.
        Interactome properties with higher priorities should be run first in any
        function that uses these properties.

        The default priority is 0. Priority collisions are okay. Since priority is defined throughout
        the codebase, it's best to see usages of this function to gauge the current range of priority.

        This is a function to prevent collisions with the reflection-based derivation of enums.
        """
        return 0

    @classmethod
    def from_interactome(cls, interactome: Interactome) -> Optional[Self]:
        ...


    @abstractmethod
    def validate_interactome(self, interactome: Interactome):
        """
        Immutably checks that an interactome has this property, raising
        an error otherwise.
        """
        checked_property = self.from_interactome(interactome)
        if checked_property is not None and self != checked_property:
            raise ValueError("The passed in interactome does not have the property {checked_property}; instead, it has {self}.")

    @abstractmethod
    def guarantee_interactome(self, interactome: Interactome):
        ...

# Note: We order derivations as so to avoid metaclass errors.
class Direction(InteractomeProperty):
    """
    The directionality of an interactome.
    """

    DIRECTED = 'directed'
    UNDIRECTED = 'undirected'
    MIXED = 'mixed'

    @staticmethod
    def priority() -> int:
        # We give Direction a higher priority
        # to ensure it gets run before GraphMultiplicity.
        # For a motivating example, see the graph on nodes A, B
        # of edges A->B and A<-B.
        return 100

    def as_letter(self) -> str:
        """
        Converts the direction to a letter, unless it is
        Direction.MIXED, in which an error is raised.
        """
        match self:
            case Direction.DIRECTED:
                return "D"
            case Direction.UNDIRECTED:
                return "U"
            case Direction.MIXED:
                raise ValueError("Direction.MIXED can not be converted to a letter.")

    @classmethod
    def from_letter(cls, string: str) -> "Direction":
        match string.upper():
            case "U":
                return Direction.UNDIRECTED
            case "D":
                return Direction.DIRECTED
            case _:
                raise ValueError(f"The value '{string}' is not one of 'U' or 'D' (case-insensitive)")

    @classmethod
    def from_interactome(cls, interactome: Interactome) -> Optional["Direction"]:
        if interactome.df.empty:
            return None

        direction_count = interactome.df["Direction"].nunique()
        if direction_count > 1:
            return Direction.MIXED

        first_direction = interactome.df["Direction"].iloc[0]
        return Direction.from_letter(first_direction)

    def validate_interactome(self, interactome: Interactome):
        if self == Direction.MIXED:
            return

        letter = self.as_letter()
        if interactome.df["Direction"].ne(letter).any():
            raise RuntimeError(f"One of the rows in the provided interactome are not '{self}'!")

    def guarantee_interactome(self, interactome: Interactome):
        match self:
            case Direction.UNDIRECTED:
                interactome.df = convert_directed_to_undirected(interactome.df)
            case Direction.DIRECTED:
                interactome.df = convert_undirected_to_directed(interactome.df)
            case Direction.MIXED:
                pass # no need to convert a mixed graph

class GraphMultiplicity(InteractomeProperty):
    """
    The multiplicity of a graph.

    Note: Multiplicity isn't biologically relevant. However, some datasets do come with
    duplicate edges as inputs. Some algorithms are tolerant to multiple edges, but others
    may need additional preprocessing to get rid of multiplicity, which is why we provide
    this interactome property.
    """

    SIMPLE = 'simple'
    MULTI = 'multi'

    def guarantee_interactome(self, interactome: Interactome):
        if self == GraphMultiplicity.MULTI:
            return

        # https://stackoverflow.com/a/25792812/7589775
        interactome.df.loc[
            (interactome.df["Interactor1"] < interactome.df["Interactor2"]) & interactome.df["Direction"] == "U",
            interactome.df.columns
        ] = interactome.df.loc[
            interactome.df["Interactor1"] < interactome.df["Interactor2"],
            ["Interactor2", "Interactor1", "Weight", "Direction"]
        ]

        # TODO: should we handle weight specially here?
        interactome.df = interactome.df.drop_duplicates(subset=["Interactor1", "Interactor2", "Direction"], keep="last")

    @classmethod
    def from_interactome(cls, interactome: Interactome) -> Optional["GraphMultiplicity"]:
        new_interactome = copy.deepcopy(interactome)
        GraphMultiplicity.SIMPLE.guarantee_interactome(new_interactome)

        if len(new_interactome.df.index) < len(interactome.df.index):
            return GraphMultiplicity.MULTI
        else:
            return GraphMultiplicity.SIMPLE

class GraphLoopiness(InteractomeProperty):
    LOOPY = 'loopy'
    NO_LOOPS = 'no_loops'

    @classmethod
    def from_interactome(cls, interactome: Interactome) -> Optional["GraphLoopiness"]:
        if (interactome.df["Interactor1"] == interactome.df["Interactor2"]).any():
            return GraphLoopiness.LOOPY
        else:
            return GraphLoopiness.NO_LOOPS

    def guarantee_interactome(self, interactome: Interactome):
        interactome.df = interactome.df[interactome.df["Interactor1"] != interactome.df["Interactor2"]]

class GraphDuals(InteractomeProperty):
    """
    Property of a graph if any two nodes are connected by two directed edges
    going the other way. It's useful to specify NO_DUALS for edge orienting algorithms.
    """

    NO_DUALS = 'no_duals'
    DUALS = 'duals'

    @staticmethod
    def construct_directed_map(interactome: Interactome) -> dict[tuple[str, str], Hashable]:
        """
        From an interactome, return all of the directed edges mapped to their indices.
        """
        directed_map: dict[tuple[str, str], Hashable] = dict()
        for index, row in interactome.df[interactome.df["Direction"] == 'D'].iterrows():
            directed_map[(row["Interactor1"], row["Interactor2"])] = index
        return directed_map

    @staticmethod
    def find_conflicts(interactome: Interactome) -> Iterable[tuple[Hashable, Hashable]]:
        """
        Returns an iterator of 2-tuples, with:
        (row to delete, row to make undirected)
        """

        directed_map = GraphDuals.construct_directed_map(interactome)

        for edge, index in directed_map.items():
            flipped_edge = (edge[1], edge[0])
            if flipped_edge in directed_map:
                yield (index, directed_map[flipped_edge])

    @classmethod
    def from_interactome(cls, interactome: Interactome) -> Optional["GraphDuals"]:
        # https://stackoverflow.com/a/3114640/7589775 iterator check for non-emptiness
        if any(True for _ in GraphDuals.find_conflicts(interactome)):
            return GraphDuals.DUALS
        else:
            return GraphDuals.NO_DUALS

    def guarantee_interactome(self, interactome: Interactome):
        conflicts = GraphDuals.find_conflicts(interactome)
        remove, undirect = [], []
        for rm, ud in conflicts:
            remove.append(rm)
            undirect.append(ud)

        interactome.df.drop(remove)
        interactome.df[interactome.df.index.isin(undirect)]["Direction"] = "U"

class Dataset:
    # Common column names
    NODE_ID = "NODEID"
    SOURCES = "sources"
    TARGETS = "targets"
    PRIZE = "prize"

    warning_threshold = 0.05  # Threshold for scarcity of columns to warn user

    def __init__(self, dataset_dict):
        self.label = None
        self.interactome: Optional[Interactome] = None
        self.node_table = None
        self.node_set = set()
        self.other_files = []
        self.load_files_from_dict(dataset_dict)
        return

    def to_file(self, file_name: str):
        """
        Saves dataset object to pickle file
        """
        with open(file_name, "wb") as f:
            pkl.dump(self, f)

    @classmethod
    def from_file(cls, file_name: str):
        """
        Loads dataset object from a pickle file.
        Usage: dataset = Dataset.from_file(pickle_file)
        """
        with open(file_name, "rb") as f:
            return pkl.load(f)

    def load_files_from_dict(self, dataset_dict):
        """
        Loads data files from dataset_dict, which is one dataset dictionary from the list
        in the config file with the fields in the config file.
        Populates node_table and interactome.

        node_table is a single merged pandas table.

        When loading data files, files of only a single column with node
        identifiers are assumed to be a binary feature where all listed nodes are
        True.

        We might want to eventually add an additional "algs" argument so only
        subsets of the entire config file are loaded, alternatively this could
        be handled outside this class.

        returns: none
        """

        self.label = dataset_dict["label"]

        # Get file paths from config
        # TODO support multiple edge files
        interactome_loc = dataset_dict["edge_files"][0]
        node_data_files = dataset_dict["node_files"]
        # edge_data_files = [""]  # Currently None
        data_loc = dataset_dict["data_dir"]

        # Load everything as pandas tables
        self.interactome = Interactome.from_file(os.path.join(data_loc, interactome_loc))
        node_set = self.interactome.get_nodes()

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
                new_col_name = node_file.split(".")[0]
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
        self.other_files = dataset_dict["other_files"]

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

    def get_interactome(self, guarantees: Iterable[InteractomeProperty]):
        """
        Gets an interactome which is guaranteed to have the provided properties.

        It is recommended to state the Direction and GraphMultiplicity,
        even if their coercions do nothing.
        """

        if self.interactome is None:
            raise ValueError("interactome is None: can't copy a non-existent interactome.")
        new_interactome = copy.deepcopy(self.interactome)

        list_guarantees = list(guarantees)
        list_guarantees.sort(key=lambda x: x.priority())
        for guarantee in list_guarantees:
            guarantee.guarantee_interactome(new_interactome)

        return new_interactome
