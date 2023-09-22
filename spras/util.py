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


# Because this is called independently for each file, the same local path can be mounted to multiple volumes
def prepare_volume(filename: Union[str, PurePath], volume_base: Union[str, PurePath]) -> Tuple[Tuple[PurePath, PurePath], str]:
    """
    Makes a file on the local file system accessible within a container by mapping the local (source) path to a new
    container (destination) path and renaming the file to be relative to the destination path.
    The destination path will be a new path relative to the volume_base that includes a hash identifier derived from the
    original filename.
    An example mapped filename looks like '/spras/MG4YPNK/oi1-edges.txt'.
    @param filename: The file on the local file system to map
    @param volume_base: The base directory in the container, which must be an absolute directory
    @return: first returned object is a tuple (source path, destination path) and the second returned object is the
    updated filename relative to the destination path
    """
    base_path = PurePosixPath(volume_base)
    if not base_path.is_absolute():
        raise ValueError(f'Volume base must be an absolute path: {volume_base}')

    if isinstance(filename, PurePath):
        filename = str(filename)

    # There's no clear way to get DEFAULT_HASH_LENGTH from config without a circular import...
    # For now, hardcoding the value to 7, since it appeared the value wasn't updated by
    # config.yaml before anyway.
    filename_hash = hash_filename(filename, 7)
    dest = PurePosixPath(base_path, filename_hash)

    abs_filename = Path(filename).resolve()
    container_filename = str(PurePosixPath(dest, abs_filename.name))
    if abs_filename.is_dir():
        dest = PurePosixPath(dest, abs_filename.name)
        src = abs_filename
    else:
        parent = abs_filename.parent
        if parent.as_posix() == '.':
            parent = Path.cwd()
        src = parent

    return (src, dest), container_filename

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
