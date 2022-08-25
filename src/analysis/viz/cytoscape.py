from pathlib import PurePath
from typing import List, Union
from src.util import prepare_volume, run_container


# TODO add Singularity support
def run_cytoscape_container(pathways: List[Union[str, PurePath]], out_dir: str) -> None:
    """
    1. take pathways and create volume mappings
    2. setup wrapper command
    3. link cytoscape src at runtime
    """
    work_dir = '/spras'

    # Each volume is a tuple (src, dest)
    volumes = list()

    # Map the output directory
    bind_path, out_dir = prepare_volume(out_dir, work_dir)
    volumes.append(bind_path)

    # Create the initial part of the Python command to run inside the container
    command = ['python', '/py4cytoscape/cytoscape_util.py',
               '--outdir', out_dir]

    # Map the pathway filenames and add them to the Python command
    # TODO need a way to preserve the original pathway names in Cytoscape
    for pathway in pathways:
        bind_path, mapped_pathway = prepare_volume(pathway, work_dir)
        volumes.append(bind_path)
        command.extend(['--files', mapped_pathway])

    print('Running Cytoscape with arguments: {}'.format(' '.join(command)), flush=True)

    # TODO consider making this a string in the config file instead of a Boolean
    #container_framework = 'singularity' if singularity else 'docker'
    container_framework = 'docker'
    # TODO set name, set remove=True?
    out = run_container(container_framework,
                        'ajshedivy/py4cy:python', # TODO switch to reedcompbio
                        command,
                        volumes,
                        work_dir)
    print(out)

    # work_dir = '/spras'
    # root = Path(__file__).parent.parent.parent.parent.absolute()
    #
    # output_dir = os.path.join(root, out_dir)
    # volumes = {
    #     output_dir: {'bind': '/spras/' + out_dir, 'mode': 'rw'}
    # }
    #
    # command = ['python', 'cytoscape_util.py', '--outdir', out_dir]
    # for pathway in pathways:
    #     command.extend(['--files', pathway])
    #
    # # Initialize a Docker client using environment variables
    # client = docker.from_env()
    #
    # try:
    #     container_output = client.containers.run(
    #         'ajshedivy/py4cy:python',
    #         command=command,
    #         remove=True,
    #         name="cyto",
    #         stderr=True,
    #         stdout=True,
    #         volumes=volumes,
    #         ports={'6080': 6080},
    #         working_dir=work_dir,
    #         detach=True)
    #     output = container_output.attach(stdout=True, stream=True, logs=True)
    #     for line in output:
    #         print(line.decode('utf-8'))
    #
    # finally:
    #     # Not sure whether this is needed
    #     client.close()
