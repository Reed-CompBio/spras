"""
Utility functions for pathway reconstruction
"""

import base64
import hashlib
import json
from pathlib import Path, PurePath, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd


def hash_params_sha1_base32(params_dict: Dict[str, Any], length: Optional[int] = None) -> str:
    """
    Hash of a dictionary.
    Derived from https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    by Nuri Cingillioglu
    Adapted to use sha1 instead of MD5 and encode in base32
    Can be truncated to the desired length
    @param params_dict: the algorithm parameters dictionary
    @param length: the length of the returned hash, which is ignored if it is None, < 1, or > the full hash length
    """
    params_hash = hashlib.sha1()
    params_encoded = json.dumps(params_dict, sort_keys=True).encode()
    params_hash.update(params_encoded)
    # base32 includes capital letters and the numbers 2-7
    # https://en.wikipedia.org/wiki/Base32#RFC_4648_Base32_alphabet
    params_base32 = base64.b32encode(params_hash.digest()).decode('ascii')
    if length is None or length < 1 or length > len(params_base32):
        return params_base32
    else:
        return params_base32[:length]


def hash_filename(filename: str, length: Optional[int] = None) -> str:
    """
    Hash of a filename using hash_params_sha1_base32
    @param filename: filename to hash
    @param length: the length of the returned hash, which is ignored if it is None, < 1, or > the full hash length
    @return: hash
    """
    return hash_params_sha1_base32({'filename': filename}, length)


def make_required_dirs(path: str):
    """
    Create the directory and parent directories required before an output file can be written to the specified path.
    Existing directories will not raise an error.
    @param path: the filename that is to be written
    """
    out_path = Path(path).parent
    out_path.mkdir(parents=True, exist_ok=True)


def add_rank_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a column of 1s to the dataframe
    @param df: the dataframe to add the rank column of 1s to
    """
    df['Rank'] = 1
    return df


def raw_pathway_df(raw_pathway_file: str, sep: str = '\t', header: int = None) -> pd.DataFrame:
    """
    Creates dataframe from contents in raw pathway file,
    otherwise returns an empty dataframe with standard output column names
    @param raw_pathway_file: path to raw_pathway_file
    @param sep: separator used when loading the dataframe, default tab character
    @param header: what row the header is in raw_pathway_file, default None
    """
    try:
        df = pd.read_csv(raw_pathway_file, sep=sep, header=header)
    except pd.errors.EmptyDataError:  # read an empty file
        df = pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction'])

    return df


def duplicate_edges(df: pd.DataFrame) -> (pd.DataFrame, bool):
    """
    Removes duplicate edges from the input DataFrame. Run within every pathway reconstruction algorithm's parse_output.
    - For duplicate edges (based on Node1, Node2, and Direction), the one with the smallest Rank is kept.
    - For undirected edges, the node pair is sorted (e.g., "B-A" becomes "A-B") before removing duplicates.

    @param df: A DataFrame from a raw file pathway.
    @return pd.DataFrame: A DataFrame with duplicate edges removed.
    @return bool: True if duplicate edges were found and removed, False otherwise.
    """
    # sort by rank, then by (node1 and node2) to ensure deterministic sorting
    df_sorted = df.sort_values(by=["Rank", "Node1", "Node2"], ascending=True, ignore_index=True)

    # for undirected edges, sort node pairs so that Node1 is always the lesser of the two
    undirected_mask = df_sorted["Direction"] == "U"

    # computes the minimum and maximum node (sorted order) for each row under the mask
    min_nodes = df_sorted.loc[undirected_mask, ["Node1", "Node2"]].min(axis=1)
    max_nodes = df_sorted.loc[undirected_mask, ["Node1", "Node2"]].max(axis=1)

    # assigns the sorted Node1 and Node2 back into the df
    df_sorted.loc[undirected_mask, "Node1"] = min_nodes
    df_sorted.loc[undirected_mask, "Node2"] = max_nodes

    unique_edges_df = df_sorted.drop_duplicates(subset=["Node1", "Node2", "Direction"], keep="first", ignore_index=True)

    return unique_edges_df, not unique_edges_df.equals(df)
