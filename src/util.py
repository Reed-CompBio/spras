"""
Utility functions for pathway reconstruction
"""

import base64
import docker
import itertools as it
import hashlib
import json
import re
import numpy as np  # Required to eval some forms of parameter ranges
from typing import Dict, Any, Optional
from pathlib import PurePath
from spython.main import Client

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


# TODO implement
# TODO add types and defaults
# TODO standardize argument terminology to match Singularity's execute and Docker's run
def run_container(framework, container, command, volume_local, volume_container, working_dir, environment):
    normalized_framework = framework.casefold()
    if normalized_framework == 'docker':
        return run_container_docker(container, command, volume_local, volume_container, working_dir, environment)
    elif normalized_framework == 'singularity':
        return run_container_singularity(container, command, volume_local, volume_container, working_dir, environment)
    else:
        raise ValueError(f'{framework} is not a recognized container framework. Choose "docker" or "singularity".')


def run_container_docker(container, command, volume_local, volume_container, working_dir, environment):
    raise NotImplementedError


def run_container_singularity(container, command, volume_local, volume_container, working_dir, environment):
    # TODO is try/finally needed for Singularity?
    singularity_options = ['--cleanenv', '--containall', '--pwd', working_dir, '--env', environment]
    return Client.execute(container,
                          command,
                          options=singularity_options,
                          bind=f'{prepare_path_docker(volume_local)}:{volume_container}')


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
        # Each set of runs should be 1 level down in the config file
        for params in alg["params"]:
            all_runs = []
            # TODO check for this key in the dict and pop
            if params == "include":
                if alg["params"][params]:
                    # This is trusting that "include" is always first
                    # This dict maps from parameter combinations hashes to parameter combination dictionaries
                    algorithm_params[alg["name"]] = dict()
                    continue
                else:
                    break
            # TODO check for this key in the dict and pop
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
                # TODO temporary workaround for yaml.safe_dump in Snakefile write_parameter_log
                for param, value in run_dict.copy().items():
                    if isinstance(value, np.float64):
                        run_dict[param] = float(value)
                params_hash = hash_params_sha1_base32(run_dict, hash_length)
                if params_hash in prior_params_hashes:
                    raise ValueError(f'Parameter hash collision detected. Increase the hash_length in the config file '
                                     f'(current length {hash_length}).')
                algorithm_params[alg["name"]][params_hash] = run_dict

    return config, datasets, out_dir, algorithm_params, algorithm_directed
