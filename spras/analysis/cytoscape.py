from pathlib import Path, PurePath
from shutil import rmtree
from typing import List, Union

from spras.util import prepare_volume, run_container


def run_cytoscape(pathways: List[Union[str, PurePath]], output_file: str, singularity: bool = False) -> None:
    """
    Create a Cytoscape session file with visualizations of each of the provided pathways
    @param pathways: a list of pathways to visualize
    @param output_file: the output Cytoscape session file
    @param singularity: whether to run in a Singularity container
    """
    work_dir = '/spras'

    # To work with Singularity, /spras must be mapped to a writeable location because that directory is fixed as
    # the home directory inside the container and Cytoscape writes configuration files there
    # $HOME cannot be set in the Dockerfile because Singularity overwrites home at launch
    env = f'HOME={work_dir}'

    # Each volume is a tuple (src, dest)
    volumes = list()

    # A temporary directory for Cytoscape output files
    cytoscape_output_dir = Path(output_file.replace('.cys', '')).absolute()
    cytoscape_output_dir.mkdir(parents=True, exist_ok=True)

    # TODO update to the latest p4cytoscape and use env variable to control the log directory instead
    # Requires generalizing the run_container function to support multiple environment variables
    volumes.append((cytoscape_output_dir, PurePath(work_dir, 'logs')))
    # Only needed when running in Singularity
    volumes.append((cytoscape_output_dir, PurePath(work_dir, 'CytoscapeConfiguration')))

    # Map the output file
    bind_path, mapped_output = prepare_volume(output_file, work_dir)
    volumes.append(bind_path)

    # Create the initial Python command to run inside the container
    command = ['python', '/py4cytoscape/cytoscape_util.py', '--output', mapped_output]

    # Map the pathway filenames and add them to the Python command
    for pathway in pathways:
        bind_path, mapped_pathway = prepare_volume(pathway, work_dir)
        volumes.append(bind_path)
        # Provided the mapped pathway file path and the original file path as the label Cytoscape
        command.extend(['--pathway', f'{mapped_pathway}|{pathway}'])

    print('Running Cytoscape with arguments: {}'.format(' '.join(command)), flush=True)

    # TODO consider making this a string in the config file instead of a Boolean
    container_framework = 'singularity' if singularity else 'docker'
    out = run_container(container_framework,
                        'reedcompbio/py4cytoscape:v3',
                        command,
                        volumes,
                        work_dir,
                        env)
    print(out)
    rmtree(cytoscape_output_dir)
