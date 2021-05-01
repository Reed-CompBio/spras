"""
Utility functions for pathway reconstruction
"""

import itertools as it
import re
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


def parse_config(config_file):
    """
    Parse the config file and return the full yaml structure as well as processed portions
    @param config_file: the path to the config file
    @return: (config, datasets, out_dir, algorithm_params)
    """
    with open(config_file) as config_f:
        config = yaml.load(config_f, Loader=yaml.FullLoader)

    # Parse dataset information
    # Datasets is a list, where each list entry has a dataset label and lists of input files
    # Need to work more on input file naming to make less strict assumptions
    # about the filename structure
    datasets = config["datasets"]
    out_dir = config["reconstruction_settings"]["locations"]["reconstruction_dir"]

    # Parse algorithm information
    # Each algorithm's parameters are provided as a list of dictionaries
    # Defaults are handled in the Python function or class that wraps
    # running that algorithm
    # Keys in the parameter dictionary are strings
    algorithm_params = dict()
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
            # We create a the product of all param combinations for each run
            param_name_list = []
            if alg["params"][params] is not None:
                for p in alg["params"][params]:
                    param_name_list.append(p)
                    all_runs.append(eval(str(alg["params"][params][p])))
            run_list_tuples = list(it.product(*all_runs))
            param_name_tuple = tuple(param_name_list)
            for r in run_list_tuples:
                run_dict = dict(zip(param_name_tuple, r))
                algorithm_params[alg["name"]].append(run_dict)

    return config, datasets, out_dir, algorithm_params
