"""
Utility functions for pathway reconstruction
"""

import base64
import itertools as it
import hashlib
import json
import re
import zlib
import numpy as np  # Required to eval some forms of parameter ranges
from typing import Dict, Any, Optional
from pathlib import PurePath

# The default length of the truncated hash used to identify parameter combinations
DEFAULT_HASH_LENGTH = 7


def prepare_path_docker(orig_path: PurePath) -> str:
    """
    Prepare an absolute path for mounting as a Docker volume.
    Converts Windows file separators to posix separators.
    Converts Windows drive letters in absolute paths.
    """
    # TODO consider testing PurePath.is_absolute()
    prepared_path = orig_path.as_posix()
    # Check whether the path matches an absolute Windows path with a drive letter
    match = re.match(r'^([A-Z]:)(.*)', prepared_path)
    if match:
        # The first group is the drive such as C:
        drive = match.group(1).lower()[0]
        # The second group is the rest of the path such as /Users/me
        prepared_path = match.group(2)
        prepared_path = '//' + drive + prepared_path
    return prepared_path


# TODO will likely delete this and use sha1_base32
def hash_params_shake(params_dict: Dict[str, Any], length: int) -> str:
    """
    Variable length hash of a dictionary.
    Derived from https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    by Nuri Cingillioglu
    Adapted to use variable length shake_128 instead of MD5
    """
    params_hash = hashlib.shake_128()
    params_encoded = json.dumps(params_dict, sort_keys=True).encode()
    params_hash.update(params_encoded)
    # length is the length of the hash digest, which is a bytes object of size length
    # return the hexadecimal representation of the bytes object
    return params_hash.hexdigest(length)


def hash_params_sha1_base32(params_dict: Dict[str, Any], length: Optional[int] = None) -> str:
    """
    Hash of a dictionary.
    Derived from https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    by Nuri Cingillioglu
    Adapted to use sha1 instead of MD5 and encode in base32
    Can be truncated to the desired length
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


# TODO will likely delete this and use sha1_base32
def hash_params_adler32(params_dict: Dict[str, Any]) -> str:
    """
    Checksum of a dictionary.
    Derived from https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    by Nuri Cingillioglu
    Adapted to use adler32 instead of MD5
    """
    params_hash = hashlib.sha1()
    params_encoded = json.dumps(params_dict, sort_keys=True).encode()
    # Could further reduce the number of characters by encoding in base32
    #base64.b32encode(zlib.adler32(params_encoded).to_bytes(4, 'big'))
    # TODO may want to zero pad to a fixed length
    return str(zlib.adler32(params_encoded))


def process_config(config):
    """
    Process the dictionary config and return the full yaml structure as well as processed portions
    @param config: configuration loaded by Snakemake, from config file and any command line arguments
    @return: (config, datasets, out_dir, algorithm_params)
    """
    if config == {}:
        raise ValueError("Config file cannot be empty. Use --configfile <filename> to set a config file.")
    out_dir = config["reconstruction_settings"]["locations"]["reconstruction_dir"]

    # Parse dataset information
    # Datasets is initially a list, where each list entry has a dataset label and lists of input files
    # Convert the dataset list into a dict where the label is the key and update the config data structure
    # TODO allow labels to be optional and assign default labels
    # TODO check for collisions in dataset labels, warn, and make the labels unique
    # Need to work more on input file naming to make less strict assumptions
    # about the filename structure
    # Currently assumes all datasets have a label and the labels are unique
    # When Snakemake parses the config file it loads the datasets as OrderedDicts not dicts
    # Convert to dicts to simplify the yaml logging
    datasets = {dataset["label"]: dict(dataset) for dataset in config["datasets"]}
    config["datasets"] = datasets

    # Code snipped from Snakefile that may be useful for assigning default labels
    # dataset_labels = [dataset.get('label', f'dataset{index}') for index, dataset in enumerate(datasets)]
    # Maps from the dataset label to the dataset list index
    # dataset_dict = {dataset.get('label', f'dataset{index}'): index for index, dataset in enumerate(datasets)}

    # Override the default parameter hash length if specified in the config file
    try:
        hash_length = int(config["hash_length"])
    except (ValueError, KeyError) as e:
        hash_length = DEFAULT_HASH_LENGTH
    prior_params_hashes = set()

    # Parse algorithm information
    # Each algorithm's parameters are provided as a list of dictionaries
    # Defaults are handled in the Python function or class that wraps
    # running that algorithm
    # Keys in the parameter dictionary are strings
    algorithm_params = dict()
    algorithm_directed = dict()
    for alg in config["algorithms"]:
        # TODO move to a separate function
        # Each set of runs should be 1 level down in the config file
        for params in alg["params"]:
            all_runs = []
            if params == "include":
                if alg["params"][params]:
                    # This is trusting that "include" is always first
                    # This dict maps from parameter combinations hashes to parameter combination dictionaries
                    algorithm_params[alg["name"]] = dict()
                    continue
                else:
                    break
            if params == "directed":
                if alg["params"][params]:
                    algorithm_directed[alg["name"]] = True
                else:
                    algorithm_directed[alg["name"]] = False
                continue
            # We create the product of all param combinations for each run
            param_name_list = []
            if alg["params"][params]:
                for p in alg["params"][params]:
                    param_name_list.append(p)
                    all_runs.append(eval(str(alg["params"][params][p])))
            run_list_tuples = list(it.product(*all_runs))
            param_name_tuple = tuple(param_name_list)
            for r in run_list_tuples:
                run_dict = dict(zip(param_name_tuple, r))
                params_hash = hash_params_sha1_base32(run_dict, hash_length)
                if params_hash in prior_params_hashes:
                    raise ValueError(f'Parameter hash collision detected. Increase the hash_length in the config file '
                                     f'(current length {hash_length}).')
                algorithm_params[alg["name"]][params_hash] = run_dict

    return config, datasets, out_dir, algorithm_params, algorithm_directed
