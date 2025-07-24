from typing import Any, Optional

from pydantic import BaseModel

# supported algorithm imports
from spras.allpairs import AllPairs
from spras.btb import BowTieBuilder
from spras.config.util import Empty
from spras.dataset import Dataset
from spras.domino import DOMINO, DominoParams
from spras.meo import MEO, MEOParams
from spras.mincostflow import MinCostFlow, MinCostFlowParams
from spras.omicsintegrator1 import OmicsIntegrator1, OmicsIntegrator1Params
from spras.omicsintegrator2 import OmicsIntegrator2, OmicsIntegrator2Params
from spras.pathlinker import PathLinker, PathLinkerParams
from spras.prm import PRM
from spras.responsenet import ResponseNet, ResponseNetParams
from spras.rwr import RWR, RWRParams
from spras.strwr import ST_RWR, ST_RWRParams

# Algorithm names to a three-tuple of (PRM, BaseModel, default BaseModel or None if there are no good defaults).
# This is used for the configuration and to fetch algorithms during reconstruction
algorithms: dict[str, tuple[type[PRM], type[BaseModel], Optional[BaseModel]]] = {
    "allpairs": (AllPairs, Empty, Empty()),
    "bowtiebuilder": (BowTieBuilder, Empty, Empty()),
    "domino": (DOMINO, DominoParams, DominoParams()),
    "meo": (MEO, MEOParams, MEOParams()),
    "mincostflow": (MinCostFlow, MinCostFlowParams, MinCostFlowParams()),
    "omicsintegrator1": (OmicsIntegrator1, OmicsIntegrator1Params, None),
    "omicsintegrator2": (OmicsIntegrator2, OmicsIntegrator2Params, OmicsIntegrator2Params()),
    "pathlinker": (PathLinker, PathLinkerParams, PathLinkerParams()),
    "responsenet": (ResponseNet, ResponseNetParams, ResponseNetParams()),
    "rwr": (RWR, RWRParams, None),
    "strwr": (ST_RWR, ST_RWRParams, None),
}

def get_algorithm(algorithm: str) -> type[PRM]:
    try:
        return algorithms[algorithm.lower()][0]
    except KeyError as exc:
        raise NotImplementedError(f'{algorithm} is not currently supported.') from exc

def run(algorithm: str, inputs, output_file, args, container_settings):
    """
    A generic interface to the algorithm-specific run functions
    """
    algorithm_runner = get_algorithm(algorithm)
    # We can't use config.config here else we would get a cyclic dependency.
    # Since args is a dict here, we use the 'run_typeless' utility PRM function.
    algorithm_runner.run_typeless(inputs, output_file, args, container_settings)


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
