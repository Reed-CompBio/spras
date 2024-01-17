"""
This config file is being used as a singleton. Because python creates a single instance
of modules when they're imported, we rely on the Snakefile instantiating the module.
In particular, when the Snakefile calls init_config, it will reassign config
to take the value of the actual config provided by Snakemake. After that point, any
module that imports this module can access a config option by checking the object's
value. For example

import spras.config as config
container_framework = config.config.container_framework

will grab the top level registry configuration option as it appears in the config file
"""

import copy as copy
import itertools as it
import os

import numpy as np
import yaml

from spras.util import hash_params_sha1_base32

# The default length of the truncated hash used to identify parameter combinations
DEFAULT_HASH_LENGTH = 7
DEFAULT_CONTAINER_PREFIX = "docker.io/reedcompbio"

config = None

# This will get called in the Snakefile, instantiating the singleton with the raw config
def init_global(config_dict):
    global config
    config = Config(config_dict)

def init_from_file(filepath):
    global config

    # Handle opening the file and parsing the yaml
    filepath = os.path.abspath(filepath)
    try:
        with open(filepath, 'r') as yaml_file:
            config_dict = yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"Error: The specified config '{filepath}' could not be found.")
        return False
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse config '{filepath}': {e}")
        return False

    # And finally, initialize
    config = Config(config_dict)


class Config:
    def __init__(self, raw_config):
        # Since process_config winds up modifying the raw_config passed to it as a side effect,
        # we'll make a deep copy here to guarantee we don't break anything. This preserves the
        # config as it's given to the Snakefile by Snakemake

        # Member vars populated by process_config. Set to None before they are populated so that our
        # __init__ makes clear exactly what is being configured.
        # Directory used for storing output
        self.out_dir = None
        # Container framework used by PRMs. Valid options are "docker" and "singularity"
        self.container_framework = None
        # The container prefix (host and organization) to use for images. Default is "docker.io/reedcompbio"
        self.container_prefix = DEFAULT_CONTAINER_PREFIX
        # A dictionary to store configured datasets against which SPRAS will be run
        self.datasets = None
        # The hash length SPRAS will use to identify parameter combinations. Default is 7
        self.hash_length = DEFAULT_HASH_LENGTH
        # The list of algorithms to run in the workflow. Each is a dict with 'name' as an expected key.
        self.algorithms = None
        # A nested dict mapping algorithm names to dicts that map parameter hashes to parameter combinations.
        # Only includes algorithms that are set to be run with 'include: true'.
        self.algorithm_params = None
        # Deprecated. Previously a dict mapping algorithm names to a Boolean tracking whether they used directed graphs.
        self.algorithm_directed  = None
        # A dict with the analysis settings
        self.analysis_params = None
        # A dict with the ML settings
        self.ml_params = None
        # A dict with the PCA settings
        self.pca_params = None
        # A dict with the hierarchical clustering settings
        self.hac_params = None
        # A Boolean specifying whether to run the summary analysis
        self.analysis_include_summary = None
        # A Boolean specifying whether to run the GraphSpace analysis
        self.analysis_include_graphspace  = None
        # A Boolean specifying whether to run the Cytoscape analysis
        self.analysis_include_cytoscape  = None
        # A Boolean specifying whether to run the ML analysis
        self.analysis_include_ml = None

        _raw_config = copy.deepcopy(raw_config)
        self.process_config(_raw_config)

    def process_config(self, raw_config):
        if raw_config == {}:
            raise ValueError("Config file cannot be empty. Use --configfile <filename> to set a config file.")

        # Set up a few top-level config variables
        self.out_dir = raw_config["reconstruction_settings"]["locations"]["reconstruction_dir"]

        # We allow the container framework not to be defined in the config. In the case it isn't, default to docker.
        # However, if we get a bad value, we raise an exception.
        if "container_framework" in raw_config:
            container_framework = raw_config["container_framework"].lower()
            if container_framework not in ("docker", "singularity"):
                msg = "SPRAS was configured to run with an unknown container framework: '" + raw_config["container_framework"] + "'. Accepted values are 'docker' or 'singularity'."
                raise ValueError(msg)
            self.container_framework = container_framework
        else:
            self.container_framework = "docker"

        # Grab registry from the config, and if none is provided default to docker
        if "container_registry" in raw_config and raw_config["container_registry"]["base_url"] != "" and raw_config["container_registry"]["owner"] != "":
            self.container_prefix = raw_config["container_registry"]["base_url"] + "/" + raw_config["container_registry"]["owner"]

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
        self.datasets = {dataset["label"]: dict(dataset) for dataset in raw_config["datasets"]}

        # Code snipped from Snakefile that may be useful for assigning default labels
        # dataset_labels = [dataset.get('label', f'dataset{index}') for index, dataset in enumerate(datasets)]
        # Maps from the dataset label to the dataset list index
        # dataset_dict = {dataset.get('label', f'dataset{index}'): index for index, dataset in enumerate(datasets)}

        # Override the default parameter hash length if specified in the config file
        if "hash_length" in raw_config and raw_config["hash_length"] != "":
            self.hash_length = int(raw_config["hash_length"])

        prior_params_hashes = set()

        # Parse algorithm information
        # Each algorithm's parameters are provided as a list of dictionaries
        # Defaults are handled in the Python function or class that wraps
        # running that algorithm
        # Keys in the parameter dictionary are strings
        self.algorithm_params = dict()
        self.algorithm_directed = dict()
        self.algorithms = raw_config["algorithms"]
        for alg in self.algorithms:
            cur_params = alg["params"]
            if "include" in cur_params and cur_params.pop("include"):
                # This dict maps from parameter combinations hashes to parameter combination dictionaries
                self.algorithm_params[alg["name"]] = dict()
            else:
                # Do not parse the rest of the parameters for this algorithm if it is not included
                continue

            if "directed" in cur_params:
                print("UPDATE: we no longer use the directed key in the config file")
                cur_params.pop("directed")

            # The algorithm has no named arguments so create a default placeholder
            if len(cur_params) == 0:
                cur_params["run1"] = {"spras_placeholder": ["no parameters"]}

            # Each set of runs should be 1 level down in the config file
            for run_params in cur_params:
                all_runs = []

                # We create the product of all param combinations for each run
                param_name_list = []
                if cur_params[run_params]:
                    for p in cur_params[run_params]:
                        param_name_list.append(p)
                        all_runs.append(eval(str(cur_params[run_params][p])))
                run_list_tuples = list(it.product(*all_runs))
                param_name_tuple = tuple(param_name_list)
                for r in run_list_tuples:
                    run_dict = dict(zip(param_name_tuple, r))
                    # TODO temporary workaround for yaml.safe_dump in Snakefile write_parameter_log
                    for param, value in run_dict.copy().items():
                        if isinstance(value, np.float64):
                            run_dict[param] = float(value)
                    params_hash = hash_params_sha1_base32(run_dict, self.hash_length)
                    if params_hash in prior_params_hashes:
                        raise ValueError(f'Parameter hash collision detected. Increase the hash_length in the config file '
                                        f'(current length {self.hash_length}).')
                    self.algorithm_params[alg["name"]][params_hash] = run_dict

        self.analysis_params = raw_config["analysis"] if "analysis" in raw_config else {}
        self.ml_params = self.analysis_params["ml"] if "ml" in self.analysis_params else {}

        self.pca_params = {}
        if "components" in self.ml_params:
            self.pca_params["components"] = self.ml_params["components"]
        if "labels" in self.ml_params:
            self.pca_params["labels"] = self.ml_params["labels"]

        self.hac_params = {}
        if "linkage" in self.ml_params:
            self.hac_params["linkage"] = self.ml_params["linkage"]
        if "metric" in self.ml_params:
            self.hac_params["metric"] = self.ml_params ["metric"]

        self.analysis_include_summary = raw_config["analysis"]["summary"]["include"]
        self.analysis_include_graphspace = raw_config["analysis"]["graphspace"]["include"]
        self.analysis_include_cytoscape = raw_config["analysis"]["cytoscape"]["include"]
        self.analysis_include_ml = raw_config["analysis"]["ml"]["include"]
