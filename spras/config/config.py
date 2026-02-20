"""
This config file is being used as a singleton. Because python creates a single instance
of modules when they're imported, we rely on the Snakefile instantiating the module.
In particular, when the Snakefile calls init_config, it will reassign config
to take the value of the actual config provided by Snakemake. After that point, any
module that imports this module can access a config option by checking the object's
value. For example

import spras.config.config as config
container_framework = config.config.container_settings.framework

will grab the top level registry configuration option as it appears in the config file
"""

import copy as copy
import functools
import hashlib
import importlib.metadata
import itertools as it
import sysconfig
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from spras.config.container_schema import ProcessedContainerSettings
from spras.config.schema import DatasetSchema, RawConfig
from spras.util import LoosePathLike, NpHashEncoder, hash_params_sha1_base32

config = None

@functools.cache
def spras_revision() -> str:
    """
    Gets the current revision of SPRAS.

    Note: This is not dependent on the SPRAS release version number nor the git commit, but rather solely on the PyPA RECORD file,
    (https://packaging.python.org/en/latest/specifications/recording-installed-packages/#the-record-file), which contains
    hashes of all of the installed SPRAS files [excluding RECORD itself], and is also included in the package distribution.
    This means that, when developing SPRAS, `spras_revision` will be updated when spras is initially installed. However, for editable
    pip installs (such as the pip installation used when developing spras), the `spras_revision` will not be updated.
    """
    try:
        site_packages_path = sysconfig.get_path("purelib") # where .dist-info is located.

        record_path = Path(
            site_packages_path,
            f"spras-{importlib.metadata.version('spras')}.dist-info",
            "RECORD"
        )
        with open(record_path, 'rb', buffering=0) as f:
            # Truncated to the magic value 8, the length of the short git revision.
            return hashlib.file_digest(f, 'sha256').hexdigest()[:8]
    except importlib.metadata.PackageNotFoundError as err:
        raise RuntimeError('spras is not an installed pip-module: did you forget to install SPRAS as a module?') from err


def attach_spras_revision(immutable_files: bool, label: str) -> str:
    """
    Attaches the SPRAS revision to a label.
    This function signature may become more complex as specific labels get versioned.

    @param label: The label to attach the SPRAS revision to.
    @param immutable_files: if False, this function is equivalent to `id`.
    """
    if immutable_files is False: return label
    # We use the `_` separator here instead of `-` as summary, analysis, and gold standard parts of the
    # Snakemake workflow process file names by splitting on hyphens to produce new jobs.
    # If this was separated with a hyphen, we would mess with that string manipulation logic.
    return f"{label}_{spras_revision()}"

# This will get called in the Snakefile, instantiating the singleton with the raw config
def init_global(config_dict):
    global config
    config = Config(config_dict)

def init_from_file(filepath):
    global config
    config = Config.from_file(filepath)


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
        # A dictionary to store configured datasets against which SPRAS will be run
        self.datasets: dict[str, DatasetSchema] = {}
        # A dictionary to store configured gold standard data against output of SPRAS runs
        self.gold_standards = None
        # The hash length SPRAS will use to identify parameter combinations.
        self.hash_length = parsed_raw_config.hash_length
        # Container settings used by PRMs.
        self.container_settings = ProcessedContainerSettings.from_container_settings(parsed_raw_config.containers, self.hash_length)
        # The list of algorithms to run in the workflow. Each is a dict with 'name' as an expected key.
        self.algorithms = None
        # A nested dict mapping algorithm names to dicts that map parameter hashes to parameter combinations.
        # Only includes algorithms that are set to be run with 'include: true'.
        self.algorithm_params: dict[str, dict[str, Any]] = dict()
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
        # Specifies whether the files should be OSDF-immutable (i.e. the file names change when the file itself changes)
        self.immutable_files = parsed_raw_config.immutable_files

        self.process_config(parsed_raw_config)

    @classmethod
    def from_file(cls, filepath: LoosePathLike):
        # Handle opening the file and parsing the yaml
        filepath = Path(filepath).absolute()
        try:
            with open(filepath, 'r') as yaml_file:
                config_dict = yaml.safe_load(yaml_file)
        except FileNotFoundError as e:
            raise RuntimeError(f"Error: The specified config '{filepath}' could not be found.") from e
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error: Failed to parse config '{filepath}'") from e

        return cls(config_dict)

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

        for dataset in raw_config.datasets:
            dataset.label = attach_spras_revision(self.immutable_files, dataset.label)
        for gold_standard in raw_config.gold_standards:
            gold_standard.label = attach_spras_revision(self.immutable_files, gold_standard.label)

        for dataset in raw_config.datasets:
            label = dataset.label
            if label.lower() in [key.lower() for key in self.datasets.keys()]:
                raise ValueError(f"Datasets must have unique case-insensitive labels, but the label {label} appears at least twice.")
            self.datasets[label] = dataset

        # parse gold standard information
        self.gold_standards = {gold_standard.label: dict(gold_standard) for gold_standard in raw_config.gold_standards}

        # check that all the dataset labels in the gold standards are existing datasets labels
        dataset_labels = set(self.datasets.keys())
        gold_standard_dataset_labels = {dataset_label for value in self.gold_standards.values() for dataset_label in value['dataset_labels']}
        for label in gold_standard_dataset_labels:
            if attach_spras_revision(self.immutable_files, label) not in dataset_labels:
                raise ValueError(f"Dataset label '{label}' provided in gold standards does not exist in the existing dataset labels.")
        # We attach the SPRAS revision to the individual dataset labels afterwards for a cleaner error message above.
        for key, gold_standard in self.gold_standards.items():
            self.gold_standards[key]["dataset_labels"] = map(
                functools.partial(attach_spras_revision, self.immutable_files),
                gold_standard["dataset_labels"]
            )

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
        self.algorithms = raw_config.algorithms
        for alg in self.algorithms:
            if alg.include:
                # This dict maps from parameter combinations hashes to parameter combination dictionaries
                self.algorithm_params[alg.name] = dict()
            else:
                # Do not parse the rest of the parameters for this algorithm if it is not included
                continue

            runs: dict[str, Any] = alg.runs

            # Each set of runs should be 1 level down in the config file
            for run_name in runs.keys():
                all_runs = []

                # We create the product of all param combinations for each run
                param_name_list = []
                # We convert our run parameters to a dictionary, allowing us to iterate over it
                run_subscriptable = vars(runs[run_name])
                for param in run_subscriptable:
                    param_name_list.append(param)
                    # this is guaranteed to be list[Any] by algorithms.py
                    param_values: list[Any] = run_subscriptable[param]
                    all_runs.append(param_values)
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
                    hash_run_dict = copy.deepcopy(run_dict)
                    if self.immutable_files:
                        # Incorporates the `spras_revision` into the hash
                        hash_run_dict["_spras_rev"] = spras_revision()
                    params_hash = hash_params_sha1_base32(hash_run_dict, self.hash_length, cls=NpHashEncoder)
                    if params_hash in prior_params_hashes:
                        raise ValueError(f'Parameter hash collision detected. Increase the hash_length in the config file '
                                        f'(current length {self.hash_length}).')

                    # We preserve the run name as it carries useful information for the parameter log,
                    # and is useful for configuration testing.
                    run_dict["_spras_run_name"] = run_name

                    self.algorithm_params[alg.name][params_hash] = run_dict

    def process_analysis(self, raw_config: RawConfig):
        if not raw_config.analysis:
            return

        # self.ml_params is a class, pca_params needs to be a dict.
        self.pca_params = {
            "components": self.ml_params.components,
            "labels": self.ml_params.labels,
            "kde": self.ml_params.kde,
            "remove_empty_pathways": self.ml_params.remove_empty_pathways
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

        # Set kde to True if Evaluation is set to True
        # When Evaluation is True, PCA is used to pick a single parameter combination for all algorithms with multiple
        # parameter combinations and KDE is used to choose the parameter combination in the PC space
        if self.analysis_include_evaluation and not self.pca_params["kde"]:
            self.pca_params["kde"] = True
            print("Setting kde to true; Evaluation analysis needs to run KDE for PCA-Chosen parameter selection.")

        # Set summary include to True if Evaluation is set to True
        # When a PCA-chosen parameter set is chosen, summary statistics are used to resolve tiebreakers.
        if self.analysis_include_evaluation and not self.analysis_include_summary:
            self.analysis_include_summary = True
            print("Setting summary include to true; Evaluation analysis needs to use summary statistics for PCA-Chosen parameter selection.")


    def process_config(self, raw_config: RawConfig):
        self.out_dir = raw_config.reconstruction_settings.locations.reconstruction_dir

        if raw_config.containers.enable_profiling and raw_config.containers.framework not in ["singularity", "apptainer"]:
            warnings.warn("enable_profiling is set to true, but the container framework is not singularity/apptainer. This setting will have no effect.", stacklevel=2)

        self.process_datasets(raw_config)
        self.process_algorithms(raw_config)
        self.process_analysis(raw_config)
