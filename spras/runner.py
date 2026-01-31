from os import PathLike
from typing import Any, Mapping, Optional

# supported algorithm imports
from spras.allpairs import AllPairs
from spras.btb import BowTieBuilder
from spras.config.container_schema import ProcessedContainerSettings
from spras.dataset import Dataset, DatasetSchema
from spras.domino import DOMINO
from spras.meo import MEO
from spras.mincostflow import MinCostFlow
from spras.omicsintegrator1 import OmicsIntegrator1
from spras.omicsintegrator2 import OmicsIntegrator2
from spras.pathlinker import PathLinker
from spras.prm import PRM
from spras.responsenet import ResponseNet
from spras.rwr import RWR
from spras.strwr import ST_RWR
from spras.util import LoosePathLike

algorithms: dict[str, type[PRM]] = {
    "allpairs": AllPairs,
    "bowtiebuilder": BowTieBuilder,
    "domino": DOMINO,
    "meo": MEO,
    "mincostflow": MinCostFlow,
    "omicsintegrator1": OmicsIntegrator1,
    "omicsintegrator2": OmicsIntegrator2,
    "pathlinker": PathLinker,
    "responsenet": ResponseNet,
    "rwr": RWR,
    "strwr": ST_RWR,
}

def get_algorithm(algorithm: str) -> type[PRM]:
    try:
        return algorithms[algorithm.lower()]
    except KeyError as exc:
        raise NotImplementedError(f'{algorithm} is not currently supported.') from exc

def run(
    algorithm: str,
    inputs: dict[str, str | PathLike],
    output_file: str | PathLike,
    args: dict[str, Any],
    container_settings: ProcessedContainerSettings,
    timeout: Optional[int]
):
    """
    A generic interface to the algorithm-specific run functions
    """
    algorithm_runner = get_algorithm(algorithm)
    # We can't use config.config here else we would get a cyclic dependency.
    # Since args is a dict here, we use the 'run_typeless' utility PRM function.
    algorithm_runner.run_typeless(inputs, output_file, args, container_settings, timeout)


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
