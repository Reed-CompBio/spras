from pathlib import PurePath
from typing import List, Union

from src.util import prepare_volume, run_container


def run_cytoscape_container(pathways: List[Union[str, PurePath]], out_dir: str, singularity: bool = False) -> None:
    """
    1. take pathways and create volume mappings
    2. setup wrapper command
    3. link cytoscape src at runtime
    """
    # To work with Singularity, /spras must be mapped to a writeable location because that directory is fixed as
    # the home directory inside the container and Cytoscape writes configuration files there
    work_dir = '/spras'

    # Each volume is a tuple (src, dest)
    volumes = list()

    # TODO update the latest p4cytoscape and use env variable to control the log directory instead
    volumes.append((PurePath(out_dir), PurePath('/spras/logs')))

    # Map the output directory
    bind_path, out_dir = prepare_volume(out_dir, work_dir)
    volumes.append(bind_path)

    # Create the initial part of the Python command to run inside the container
    command = ['python', '/py4cytoscape/cytoscape_util.py',
               '--outdir', out_dir,
               '--outlabel', 'cytoscape-session']

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
                        'reedcompbio/py4cytoscape',
                        command,
                        volumes,
                        work_dir)
    print(out)
