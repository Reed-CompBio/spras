"""
Utility functions for pathway reconstruction
"""

import itertools as it
import re
import numpy as np  # Required to eval some forms of parameter ranges
from pathlib import PurePath
import yaml


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


def process_config(config):
    """
    Process the dictionary config and return the full yaml structure as well as processed portions
    @param config: configuration loaded by Snakemake, from config file and any command line arguments
    @return: (config, datasets, out_dir, algorithm_params)
    """

    out_dir = config["reconstruction_settings"]["locations"]["reconstruction_dir"]

    # Parse dataset information
    # Datasets is initially a list, where each list entry has a dataset label and lists of input files
    # Convert the dataset list into a dict where the label is the key and update the config data structure
    # TODO allow labels to be optional and assign default labels
    # TODO check for collisions in dataset labels, warn, and make the labels unique
    # Need to work more on input file naming to make less strict assumptions
    # about the filename structure
    # Currently assumes all datasets have a label and the labels are unique
    datasets = {dataset["label"]: dataset for dataset in config["datasets"]}
    config["datasets"] = datasets

    # Code snipped from Snakefile that may be useful for assigning default labels
    # dataset_labels = [dataset.get('label', f'dataset{index}') for index, dataset in enumerate(datasets)]
    # Maps from the dataset label to the dataset list index
    # dataset_dict = {dataset.get('label', f'dataset{index}'): index for index, dataset in enumerate(datasets)}

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
            if params == "include":
                if alg["params"][params]:
                    # This is trusting that "include" is always first
                    algorithm_params[alg["name"]] = []
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
                algorithm_params[alg["name"]].append(run_dict)

    return config, datasets, out_dir, algorithm_params, algorithm_directed
