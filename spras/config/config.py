"""
This config file is being used as a singleton. Because python creates a single instance
of modules when they're imported, we rely on the Snakefile instantiating the module.
In particular, when the Snakefile calls init_config, it will reassign config
to take the value of the actual config provided by Snakemake. After that point, any
module that imports this module can access a config option by checking the object's
value. For example

import spras.config.config as config
container_framework = config.config.container_framework

will grab the top level registry configuration option as it appears in the config file
"""

import copy as copy
import itertools as it
import os
import re
import warnings
from collections.abc import Iterable
from typing import Any

import numpy as np
import yaml

from spras.config.container_schema import ProcessedContainerOptions
from spras.config.schema import Analysis, RawConfig
from spras.util import NpHashEncoder, hash_params_sha1_base32

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
    except FileNotFoundError as e:
        raise RuntimeError(f"Error: The specified config '{filepath}' could not be found.") from e
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error: Failed to parse config '{filepath}'") from e

    # And finally, initialize
    config = Config(config_dict)


class Config:
    def __init__(self, raw_config: dict[str, Any]):
        # Since snakemake provides an empty config, we provide this
        # wrapper error first before passing validation to pydantic.
        if raw_config == {}:
            raise ValueError("Config file cannot be empty. Use --configfile <filename> to set a config file.")

        parsed_raw_config = RawConfig.model_validate(raw_config)

        # Member vars populated by process_config. Any values that don't have quick initial values are set to None
        # before they are populated for __init__ to show exactly what is being configured.

        # Directory used for storing output
        self.out_dir = parsed_raw_config.reconstruction_settings.locations.reconstruction_dir
        # Container framework used by PRMs. Valid options are "docker", "dsub", and "singularity"
        self.container_settings = ProcessedContainerOptions.from_container_settings(parsed_raw_config.containers, parsed_raw_config.hash_length)
        # A Boolean specifying whether to unpack singularity containers. Default is False
        self.unpack_singularity = False
        # A dictionary to store configured datasets against which SPRAS will be run
        self.datasets = None
        # A dictionary to store configured gold standard data against output of SPRAS runs
        self.gold_standards = None
        # The hash length SPRAS will use to identify parameter combinations.
        self.hash_length = parsed_raw_config.hash_length
        # The list of algorithms to run in the workflow. Each is a dict with 'name' as an expected key.
        self.algorithms = None
        # A nested dict mapping algorithm names to dicts that map parameter hashes to parameter combinations.
        # Only includes algorithms that are set to be run with 'include: true'.
        self.algorithm_params = None
        # Deprecated. Previously a dict mapping algorithm names to a Boolean tracking whether they used directed graphs.
        self.algorithm_directed = None
        # A dict with the analysis settings
        self.analysis_params = parsed_raw_config.analysis
        # A dict with the evaluation settings
        self.evaluation_params = self.analysis_params.evaluation
        # A dict with the ML settings
        self.ml_params = self.analysis_params.ml
        # A Boolean specifying whether to run ML analysis for individual algorithms
        self.analysis_include_ml_aggregate_algo = None
        # A dict with the PCA settings
        self.pca_params = None
        # A dict with the hierarchical clustering settings
        self.hac_params = None
        # A Boolean specifying whether to run the summary analysis
        self.analysis_include_summary = None
        # A Boolean specifying whether to run the Cytoscape analysis
        self.analysis_include_cytoscape = None
        # A Boolean specifying whether to run the ML analysis
        self.analysis_include_ml = None
        # A Boolean specifying whether to run the Evaluation analysis
        self.analysis_include_evaluation = None
        # A Boolean specifying whether to run the ML per algorithm analysis
        self.analysis_include_ml_aggregate_algo = None
        # A Boolean specifying whether to run the evaluation per algorithm analysis
        self.analysis_include_evaluation_aggregate_algo = None

        self.process_config(parsed_raw_config)

    def process_datasets(self, raw_config: RawConfig):
        """
        Parse dataset information
        Datasets is initially a list, where each list entry has a dataset label and lists of input files
        Convert the dataset list into a dict where the label is the key and update the config data structure
        """
        # TODO allow labels to be optional and assign default labels
        # Need to work more on input file naming to make less strict assumptions
        # about the filename structure
        # Currently assumes all datasets have a label and the labels are unique
        # When Snakemake parses the config file it loads the datasets as OrderedDicts not dicts
        # Convert to dicts to simplify the yaml logging
        self.datasets = {}
        for dataset in raw_config.datasets:
            label = dataset.label
            if label.lower() in [key.lower() for key in self.datasets.keys()]:
                raise ValueError(f"Datasets must have unique case-insensitive labels, but the label {label} appears at least twice.")
            self.datasets[label] = dict(dataset)

        # parse gold standard information
        self.gold_standards = {gold_standard.label: dict(gold_standard) for gold_standard in raw_config.gold_standards}

        # check that all the dataset labels in the gold standards are existing datasets labels
        dataset_labels = set(self.datasets.keys())
        gold_standard_dataset_labels = {dataset_label for value in self.gold_standards.values() for dataset_label in value['dataset_labels']}
        for label in gold_standard_dataset_labels:
            if label not in dataset_labels:
                raise ValueError(f"Dataset label '{label}' provided in gold standards does not exist in the existing dataset labels.")

        # Code snipped from Snakefile that may be useful for assigning default labels
        # dataset_labels = [dataset.get('label', f'dataset{index}') for index, dataset in enumerate(datasets)]
        # Maps from the dataset label to the dataset list index
        # dataset_dict = {dataset.get('label', f'dataset{index}'): index for index, dataset in enumerate(datasets)}

    def process_algorithms(self, raw_config: RawConfig):
        """
        Parse algorithm information
        Each algorithm's parameters are provided as a list of dictionaries
        Defaults are handled in the Python function or class that wraps
        running that algorithm
        Keys in the parameter dictionary are strings
        """
        prior_params_hashes = set()
        self.algorithm_params = dict()
        self.algorithm_directed = dict()
        self.algorithms = raw_config.algorithms
        for alg in self.algorithms:
            cur_params = alg.params
            if cur_params.include:
                # This dict maps from parameter combinations hashes to parameter combination dictionaries
                self.algorithm_params[alg.name] = dict()
            else:
                # Do not parse the rest of the parameters for this algorithm if it is not included
                continue

            if cur_params.directed is not None:
                warnings.warn("UPDATE: we no longer use the directed key in the config file", stacklevel=2)

            cur_params = cur_params.__pydantic_extra__
            if cur_params is None:
                raise RuntimeError("An internal error occured: ConfigDict extra should be set on AlgorithmParams.")

            # The algorithm has no named arguments so create a default placeholder
            if len(cur_params.keys()) == 0:
                cur_params["run1"] = {"spras_placeholder": ["no parameters"]}

            # Each set of runs should be 1 level down in the config file
            for run_params in cur_params:
                all_runs = []

                # We create the product of all param combinations for each run
                param_name_list = []
                if cur_params[run_params]:
                    for p in cur_params[run_params]:
                        param_name_list.append(p)
                        obj = str(cur_params[run_params][p])
                        try:
                            obj = [int(obj)]
                        except ValueError:
                            try:
                                obj = [float(obj)]
                            except ValueError:
                                # Handles arrays and special evaluation types
                                # TODO: do we want to explicitly bar `eval` if we may use untrusted user inputs later?
                                if obj.startswith(("range", "np.linspace", "np.arange", "np.logspace", "[")):
                                    obj = eval(obj)
                                elif obj.lower() == "true":
                                    obj = [True]
                                elif obj.lower() == "false":
                                    obj = [False]
                                else:
                                    # Catch-all for strings
                                    obj = [obj]
                            if not isinstance(obj, Iterable):
                                raise ValueError(f"The object `{obj}` in algorithm {alg.name} at key '{p}' in run '{run_params}' is not iterable!") from None
                        all_runs.append(obj)
                run_list_tuples = list(it.product(*all_runs))
                param_name_tuple = tuple(param_name_list)
                for r in run_list_tuples:
                    run_dict = dict(zip(param_name_tuple, r, strict=True))
                    # TODO: Workaround for yaml.safe_dump in Snakefile write_parameter_log.
                    # We would like to preserve np info for larger floats and integers on the config,
                    # but this isn't strictly necessary for the pretty yaml logging that's happening - if we
                    # want to preserve the precision, we need to output this into yaml as strings.
                    for param, value in run_dict.copy().items():
                        if isinstance(value, np.integer):
                            run_dict[param] = int(value)
                        if isinstance(value, np.floating):
                            run_dict[param] = float(value)
                        if isinstance(value, np.ndarray):
                            run_dict[param] = value.tolist()
                    params_hash = hash_params_sha1_base32(run_dict, self.hash_length, cls=NpHashEncoder)
                    if params_hash in prior_params_hashes:
                        raise ValueError(f'Parameter hash collision detected. Increase the hash_length in the config file '
                                        f'(current length {self.hash_length}).')
                    self.algorithm_params[alg.name][params_hash] = run_dict

    def process_analysis(self, raw_config: RawConfig):
        if not raw_config.analysis:
            return

        # self.ml_params is a class, pca_params needs to be a dict.
        self.pca_params = {
            "components": self.ml_params.components,
            "labels": self.ml_params.labels
        }

        self.hac_params = {
            "linkage": self.ml_params.linkage,
            "metric": self.ml_params.metric
        }

        self.analysis_include_summary = raw_config.analysis.summary.include
        self.analysis_include_cytoscape = raw_config.analysis.cytoscape.include
        self.analysis_include_ml = raw_config.analysis.ml.include
        self.analysis_include_evaluation = raw_config.analysis.evaluation.include

        # Only run ML aggregate per algorithm if analysis include ML is set to True
        if self.ml_params.aggregate_per_algorithm and self.analysis_include_ml:
            self.analysis_include_ml_aggregate_algo = raw_config.analysis.ml.aggregate_per_algorithm
        else:
            self.analysis_include_ml_aggregate_algo = False

        # Raises an error if Evaluation is enabled but no gold standard data is provided
        if self.gold_standards == {} and self.analysis_include_evaluation:
            raise ValueError("Evaluation analysis cannot run as gold standard data not provided. "
                             "Please set evaluation include to false or provide gold standard data.")

        # Only run Evaluation if ML is set to True
        if not self.analysis_include_ml:
            self.analysis_include_evaluation = False

        # Only run Evaluation aggregate per algorithm if analysis include ML is set to True
        if self.evaluation_params.aggregate_per_algorithm and self.analysis_include_evaluation:
            self.analysis_include_evaluation_aggregate_algo = raw_config.analysis.evaluation.aggregate_per_algorithm
        else:
            self.analysis_include_evaluation_aggregate_algo = False

        # Only run Evaluation per algorithm if ML per algorithm is set to True
        if not self.analysis_include_ml_aggregate_algo:
            self.analysis_include_evaluation_aggregate_algo = False

    def process_config(self, raw_config: RawConfig):
        self.out_dir = raw_config.reconstruction_settings.locations.reconstruction_dir

        self.process_datasets(raw_config)
        self.process_algorithms(raw_config)
        self.process_analysis(raw_config)
