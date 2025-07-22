from typing import Any

# supported algorithm imports
from spras.allpairs import AllPairs
from spras.btb import BowTieBuilder
from spras.dataset import Dataset
from spras.domino import DOMINO
from spras.meo import MEO
from spras.mincostflow import MinCostFlow
from spras.omicsintegrator1 import OmicsIntegrator1
from spras.omicsintegrator2 import OmicsIntegrator2
from spras.pathlinker import PathLinker
from spras.prm import PRM
from spras.robust import ROBUST
from spras.rwr import RWR
from spras.strwr import ST_RWR

algorithms: dict[str, type[PRM]] = {
    "allpairs": AllPairs,
    "bowtiebuilder": BowTieBuilder,
    "domino": DOMINO,
    "meo": MEO,
    "mincostflow": MinCostFlow,
    "omicsintegrator1": OmicsIntegrator1,
    "omicsintegrator2": OmicsIntegrator2,
    "pathlinker": PathLinker,
    "robust": ROBUST,
    "rwr": RWR,
    "strwr": ST_RWR,
}

def get_algorithm(algorithm: str) -> type[PRM]:
    try:
        return algorithms[algorithm.lower()]
    except KeyError as exc:
        raise NotImplementedError(f'{algorithm} is not currently supported.') from exc

def run(algorithm: str, params):
    """
    A generic interface to the algorithm-specific run functions
    """
    algorithm_runner = get_algorithm(algorithm)
    algorithm_runner.run(**params)


def get_required_inputs(algorithm: str):
    """
    Get the input files requires to run this algorithm
    @param algorithm: algorithm name
    @return: A list of strings of input files types
    """
    algorithm_runner = get_algorithm(algorithm)
    return algorithm_runner.required_inputs


def merge_input(dataset_dict, dataset_file: str):
    """
    Merge files listed for this dataset and write the dataset to disk
    @param dataset_dict: dataset to process
    @param dataset_file: output filename
    """
    dataset = Dataset(dataset_dict)
    dataset.to_file(dataset_file)


def prepare_inputs(algorithm: str, data_file: str, filename_map: dict[str, str]):
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


def parse_output(algorithm: str, raw_pathway_file: str, standardized_pathway_file: str, params: dict[str, Any]):
    """
    Convert a predicted pathway into the universal format
    @param algorithm: algorithm name
    @param raw_pathway_file: pathway file produced by an algorithm's run function
    @param standardized_pathway_file: the same pathway written in the universal format
    """
    algorithm_runner = get_algorithm(algorithm)
    return algorithm_runner.parse_output(raw_pathway_file, standardized_pathway_file, params)
