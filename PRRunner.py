import Dataset

# supported algorithm imports
from src.meo import MEO as meo
from src.omicsintegrator1 import OmicsIntegrator1 as omicsintegrator1
from src.omicsintegrator2 import OmicsIntegrator2 as omicsintegrator2
from src.pathlinker import PathLinker as pathlinker

def run(algorithm, params):
    """
    A generic interface to the algorithm-specific run functions
    """
    try:
        algorithm_runner = globals()[algorithm.lower()]
    except KeyError:
        raise NotImplementedError(f'{algorithm} is not currently supported')
    algorithm_runner.run(**params)


def get_required_inputs(algorithm):
    """
    Get the input files requires to run this algorithm
    @param algorithm: algorithm name
    @return: A list of strings of input files types
    """
    try:
        algorithm_runner = globals()[algorithm.lower()]
    except KeyError:
        raise NotImplementedError(f'{algorithm} is not currently supported')
    return algorithm_runner.required_inputs


def merge_input(dataset_dict, dataset_file):
    """
    Merge files listed for this dataset and write the dataset to disk
    @param dataset_dict: dataset to process
    @param dataset_file: output filename
    """
    dataset = Dataset.Dataset(dataset_dict)
    dataset.to_file(dataset_file)


def prepare_inputs(algorithm, data_file, filename_map):
    """
    Prepare general dataset files for this algorithm
    @param algorithm: algorithm name
    @param data_file: dataset
    @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
    @return:
    """
    dataset = Dataset.Dataset.from_file(data_file)
    try:
        algorithm_runner = globals()[algorithm.lower()]
    except KeyError:
        raise NotImplementedError(f'{algorithm} is not currently supported')
    return algorithm_runner.generate_inputs(dataset, filename_map)


def parse_output(algorithm, raw_pathway_file, standardized_pathway_file):
    """
    Convert a predicted pathway into the universal format
    @param algorithm: algorithm name
    @param raw_pathway_file: pathway file produced by an algorithm's run function
    @param standardized_pathway_file: the same pathway written in the universal format
    """
    try:
        algorithm_runner = globals()[algorithm.lower()]
    except KeyError:
        raise NotImplementedError(f'{algorithm} is not currently supported')
    return algorithm_runner.parse_output(raw_pathway_file, standardized_pathway_file)
