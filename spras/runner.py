import copy
import importlib
from typing import Any, Mapping

from spras.config.dataset import DatasetSchema
from spras.config.util import ALGORITHM_REGISTRY, AlgorithmName
from spras.dataset import Dataset
from spras.prm import PRM
from spras.util import LoosePathLike


def _load_algorithms() -> dict[AlgorithmName, type[PRM]]:
    """Load all algorithm classes from ALGORITHM_REGISTRY via importlib."""
    result = {}
    for name, (module_path, class_name) in ALGORITHM_REGISTRY.items():
        mod = importlib.import_module(module_path)
        result[AlgorithmName(name)] = getattr(mod, class_name)
    return result


# Eagerly load all algorithm classes once at import time so every call to
# get_algorithm() is a cheap dict lookup rather than a repeated importlib call.
algorithms = _load_algorithms()

def get_algorithm(algorithm: str) -> type[PRM]:
    try:
        algo_enum = AlgorithmName(algorithm)
        return algorithms[algo_enum]
    except (ValueError, KeyError) as exc:
        raise NotImplementedError(f'{algorithm} is not currently supported.') from exc

def run(algorithm: str, inputs, output_file, args, container_settings):
    """
    A generic interface to the algorithm-specific run functions
    """
    algorithm_runner = get_algorithm(algorithm)
    # Resolve per-algorithm image override so containers.py can use it
    settings = copy.copy(container_settings)
    if settings.images and algorithm in settings.images:
        settings.image_override = settings.images[algorithm]
    # We can't use config.config here else we would get a cyclic dependency.
    # Since args is a dict here, we use the 'run_typeless' utility PRM function.
    algorithm_runner.run_typeless(inputs, output_file, args, settings)


def get_required_inputs(algorithm: str):
    """
    Get the input files requires to run this algorithm
    @param algorithm: algorithm name
    @return: A list of strings of input files types
    """
    algorithm_runner = get_algorithm(algorithm)
    return algorithm_runner.required_inputs


def merge_input(dataset_data: DatasetSchema, dataset_output: LoosePathLike):
    """
    Merge files listed for this dataset and write the dataset to disk
    @param dataset_dict: dataset to process
    @param dataset_file: output filename
    """
    dataset = Dataset(dataset_data)
    dataset.to_file(dataset_output)


def prepare_inputs(algorithm: str, data_file: LoosePathLike, filename_map: Mapping[str, LoosePathLike]):
    """
    Prepare general dataset files for this algorithm
    @param algorithm: algorithm name
    @param data_file: dataset
    @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
    @return:
    """
    dataset = Dataset.from_file(data_file)
    algorithm_runner = get_algorithm(algorithm)
    return algorithm_runner.generate_inputs(dataset, filename_map)


# TODO: make raw_pathway_file and standardized_pathway_file LoosePathLike
def parse_output(algorithm: str, raw_pathway_file: str, standardized_pathway_file: str, params: Mapping[str, Any]):
    """
    Convert a predicted pathway into the universal format
    @param algorithm: algorithm name
    @param raw_pathway_file: pathway file produced by an algorithm's run function
    @param standardized_pathway_file: the same pathway written in the universal format
    """
    algorithm_runner = get_algorithm(algorithm)
    return algorithm_runner.parse_output(raw_pathway_file, standardized_pathway_file, params)
