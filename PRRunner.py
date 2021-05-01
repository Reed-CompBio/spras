import Dataset

# supported algorithm imports
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


def prepare_inputs(input_pref, algorithm, data_file, params):
    """
    Prepare general dataset files for this algorithm
    @param input_pref:
    @param algorithm: algorithm name
    @param data_file:
    @param params:
    @return:
    """
    dataset = Dataset.Dataset.from_file(data_file)
    try:
        algorithm_runner = globals()[algorithm.lower()]
    except KeyError:
        raise NotImplementedError(f'{algorithm} is not currently supported')
    return_val = algorithm_runner.generate_inputs(dataset, input_pref, params)
    return return_val
