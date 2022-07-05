import os
from pathlib import Path, PurePath
from typing import List, Union
import docker


def run_cytoscape_container(pathways: List[Union[str, PurePath]], out_dir: str) -> None:
    '''
    1. take pathways and create volume mappings
    2. setup wrapper command 
    3. link cytoscape src at runtime
    
    '''
    print(out_dir)

    work_dir        = '/spras'
    root            = Path(__file__).parent.parent.parent.parent.absolute()

    output_dir      = os.path.join(root, out_dir)
    volumes = {
        output_dir : {'bind': '/spras/'+out_dir, 'mode': 'rw'}
    }

    command = ['python', 'cytoscape_util.py', '--outdir', out_dir]
    for pathway in pathways:
        command.extend(['--files', pathway])

    # Initialize a Docker client using environment variables
    client = docker.from_env()

    print('run container')
    try:
        container_output = client.containers.run(
            'ajshedivy/py4cy:python',
            command=command,
            remove=True,
            name="cyto",
            stderr=True,
            stdout=True,
            volumes=volumes,
            ports={'6080':6080},
            working_dir=work_dir,
            detach=True)
        output = container_output.attach(stdout=True, stream=True, logs=True)
        for line in output:
            print(line.decode('utf-8'))

    finally:
        # Not sure whether this is needed
        client.close()
