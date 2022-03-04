"""
Utility functions for pathway reconstruction
"""

import base64
import docker
import itertools as it
import hashlib
import json
import re
import os
import platform
import numpy as np  # Required to eval some forms of parameter ranges
from typing import Dict, Any, Optional
from pathlib import Path, PurePath, PurePosixPath

# The default length of the truncated hash used to identify parameter combinations
DEFAULT_HASH_LENGTH = 7


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


# Convert a file_path that is in src_path to be in dest_path instead
def convert_docker_path(src_path, dest_path, file_path):
    rel_path = file_path.relative_to(src_path)
    return PurePosixPath(dest_path, rel_path)


# TODO add types and defaults
# TODO standardize argument terminology to match Singularity's execute and Docker's run
def run_container(framework, container, command, volumes, working_dir, environment):
    normalized_framework = framework.casefold()
    if normalized_framework == 'docker':
        return run_container_docker(container, command, volumes, working_dir, environment)
    elif normalized_framework == 'singularity':
        return run_container_singularity(container, command, volumes, working_dir, environment)
    else:
        raise ValueError(f'{framework} is not a recognized container framework. Choose "docker" or "singularity".')


# TODO any issue with creating a new client each time inside this function?
# TODO environment currently a single string (e.g. 'TMPDIR=/OmicsIntegrator1'), should it be a list?
def run_container_docker(container, command, volumes, working_dir, environment):
    out = None
    try:
        # Initialize a Docker client using environment variables
        client = docker.from_env()
        # Track the contents of the local directories that will be bound so that new files added can have their owner
        # changed
        pre_volume_contents = {}
        src_dest_map = {}
        for src, dest in volumes:
            src_path = Path(src)
            # The same source path can be in volumes more than once if there were multiple input or output files
            # in the same directory
            # Only check each unique source path once and track which of the possible destination paths was used
            if src_path not in pre_volume_contents:
                # Only list files in the directory, do not walk recursively because it could include
                # a massive number of files
                pre_volume_contents[src_path] = set(src_path.iterdir())
                src_dest_map[src_path] = dest
        print(f'Pre-Docker volume contents:\n{pre_volume_contents}')

        bind_paths = [f'{prepare_path_docker(src)}:{dest}' for src, dest in volumes]
        print(f'Bind paths: {bind_paths}')

        out = client.containers.run(container,
                                    command,
                                    stderr=True,
                                    volumes=bind_paths,
                                    working_dir=working_dir,
                                    environment=[environment]).decode('utf-8')

        # TODO does this cleanup need to still run even if there was an error in the above run command?
        # On Unix, files written by the above Docker run command will be owned by root and cannot be modified
        # outside the container by a non-root user
        # Reset the file owner and the group inside the container
        try:
            # Only available on Unix
            uid = os.getuid()
            gid = os.getgid()

            all_modified_volume_contents = set()
            for src_path in pre_volume_contents.keys():
                print(f'Checking source path: {src_path}')
                # Assumes the Docker run call is the only process that modified the contents
                # Only considers files that were added, not files that were modified
                post_volume_contents = set(src_path.iterdir())
                print(f'Post-Docker volume contents: {post_volume_contents}')
                modified_volume_contents = post_volume_contents - pre_volume_contents[src_path]
                print(f'Local files modified by Docker run call: {modified_volume_contents}')
                modified_volume_contents = [str(convert_docker_path(src_path, src_dest_map[src_path], p)) for p in
                                            modified_volume_contents]
                print(f'Converted local files modified by Docker run call: {modified_volume_contents}')
                all_modified_volume_contents.update(modified_volume_contents)
            print(f'Found {len(all_modified_volume_contents)} paths to update ownership')

            # This command changes the ownership of output files so we don't
            # get a permissions error when snakemake or the user try to touch the files
            # Use --recursive because new directories could have been created inside the container
            # TODO remove --verbose
            chown_command = ['chown', f'{uid}:{gid}', '--verbose', '--recursive']
            chown_command.extend(all_modified_volume_contents)
            chown_command = ' '.join(chown_command)
            print(f'chown command: {chown_command}')
            client.containers.run(container,
                                  chown_command,
                                  stderr=True,
                                  volumes=bind_paths,
                                  working_dir=working_dir,
                                  environment=[environment]).decode('utf-8')
        # Raised on non-Unix systems
        except AttributeError:
            pass
        return out
    except Exception as err:
        print(err)
    finally:
        # Not sure whether this is needed
        client.close()
        # TODO what to return in this case
        return out


def run_container_singularity(container, command, volumes, working_dir, environment):
    # spython is not compatible with Windows
    if platform.system() != 'Linux':
        raise NotImplementedError('Singularity support is only available on Linux')

    # See https://stackoverflow.com/questions/3095071/in-python-what-happens-when-you-import-inside-of-a-function
    from spython.main import Client

    bind_paths = [f'{prepare_path_docker(src)}:{dest}' for src, dest in volumes]
    print(f'Bind paths: {bind_paths}')

    # TODO is try/finally needed for Singularity?
    singularity_options = ['--cleanenv', '--containall', '--pwd', working_dir, '--env', environment]
    # Adding 'docker://' to the container indicates this is a Docker image Singularity must convert
    return Client.execute('docker://' + container,
                          command,
                          options=singularity_options,
                          bind=bind_paths)


def hash_params_sha1_base32(params_dict: Dict[str, Any], length: Optional[int] = None) -> str:
    """
    Hash of a dictionary.
    Derived from https://www.doc.ic.ac.uk/~nuric/coding/how-to-hash-a-dictionary-in-python.html
    by Nuri Cingillioglu
    Adapted to use sha1 instead of MD5 and encode in base32
    Can be truncated to the desired length
    @param params_dict: the algorithm parameters dictionary
    @param length: the length of the returned hash, which is ignored if it is None, < 1, or > the full hash length
    """
    params_hash = hashlib.sha1()
    params_encoded = json.dumps(params_dict, sort_keys=True).encode()
    params_hash.update(params_encoded)
    # base32 includes capital letters and the numbers 2-7
    # https://en.wikipedia.org/wiki/Base32#RFC_4648_Base32_alphabet
    params_base32 = base64.b32encode(params_hash.digest()).decode('ascii')
    if length is None or length < 1 or length > len(params_base32):
        return params_base32
    else:
        return params_base32[:length]


def hash_filename(filename: str, length: Optional[int] = None) -> str:
    """
    Hash of a filename using hash_params_sha1_base32
    @param filename: filename to hash
    @param length: the length of the returned hash, which is ignored if it is None, < 1, or > the full hash length
    @return: hash
    """
    return hash_params_sha1_base32({'filename': filename}, length)


# TODO docstring once working as expected
# TODO because this is called independently for each file, the same local path can be mounted to multiple volumes
def prepare_volume(filename: str, volume_base: str):
    base_path = PurePosixPath(volume_base)
    if not base_path.is_absolute():
        raise ValueError(f'Volume base must be an absolute path: {volume_base}')

    filename_hash = hash_filename(filename, DEFAULT_HASH_LENGTH)
    dest = PurePosixPath(base_path, filename_hash)

    abs_filename = Path(filename).resolve()
    container_filename = str(PurePosixPath(dest, abs_filename.name))
    if abs_filename.is_dir():
        dest = PurePosixPath(dest, abs_filename.name)
        #src = prepare_path_docker(abs_filename)
        src = abs_filename
    else:
        parent = abs_filename.parent
        if parent.as_posix() == '.':
            parent = Path.cwd()
        #src = prepare_path_docker(parent)
        src = parent

    print(f'Renaming {filename} to {container_filename}')
    print(f'Mounting volume {src} to {dest}')
    return (src, dest), container_filename


def process_config(config):
    """
    Process the dictionary config and return the full yaml structure as well as processed portions
    @param config: configuration loaded by Snakemake, from config file and any command line arguments
    @return: (config, datasets, out_dir, algorithm_params)
    """
    if config == {}:
        raise ValueError("Config file cannot be empty. Use --configfile <filename> to set a config file.")
    out_dir = config["reconstruction_settings"]["locations"]["reconstruction_dir"]

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
    datasets = {dataset["label"]: dict(dataset) for dataset in config["datasets"]}
    config["datasets"] = datasets

    # Code snipped from Snakefile that may be useful for assigning default labels
    # dataset_labels = [dataset.get('label', f'dataset{index}') for index, dataset in enumerate(datasets)]
    # Maps from the dataset label to the dataset list index
    # dataset_dict = {dataset.get('label', f'dataset{index}'): index for index, dataset in enumerate(datasets)}

    # Override the default parameter hash length if specified in the config file
    try:
        hash_length = int(config["hash_length"])
    except (ValueError, KeyError) as e:
        hash_length = DEFAULT_HASH_LENGTH
    prior_params_hashes = set()

    # Parse algorithm information
    # Each algorithm's parameters are provided as a list of dictionaries
    # Defaults are handled in the Python function or class that wraps
    # running that algorithm
    # Keys in the parameter dictionary are strings
    algorithm_params = dict()
    algorithm_directed = dict()
    for alg in config["algorithms"]:
        # Each set of runs should be 1 level down in the config file
        for params in alg["params"]:
            all_runs = []
            # TODO check for this key in the dict and pop
            if params == "include":
                if alg["params"][params]:
                    # This is trusting that "include" is always first
                    # This dict maps from parameter combinations hashes to parameter combination dictionaries
                    algorithm_params[alg["name"]] = dict()
                    continue
                else:
                    break
            # TODO check for this key in the dict and pop
            if params == "directed":
                if alg["params"][params]:
                    algorithm_directed[alg["name"]] = True
                else:
                    algorithm_directed[alg["name"]] = False
                continue
            # We create the product of all param combinations for each run
            param_name_list = []
            if alg["params"][params]:
                for p in alg["params"][params]:
                    param_name_list.append(p)
                    all_runs.append(eval(str(alg["params"][params][p])))
            run_list_tuples = list(it.product(*all_runs))
            param_name_tuple = tuple(param_name_list)
            for r in run_list_tuples:
                run_dict = dict(zip(param_name_tuple, r))
                # TODO temporary workaround for yaml.safe_dump in Snakefile write_parameter_log
                for param, value in run_dict.copy().items():
                    if isinstance(value, np.float64):
                        run_dict[param] = float(value)
                params_hash = hash_params_sha1_base32(run_dict, hash_length)
                if params_hash in prior_params_hashes:
                    raise ValueError(f'Parameter hash collision detected. Increase the hash_length in the config file '
                                     f'(current length {hash_length}).')
                algorithm_params[alg["name"]][params_hash] = run_dict

    return config, datasets, out_dir, algorithm_params, algorithm_directed
