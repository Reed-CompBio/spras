from pathlib import PurePath
import sys
from typing import List, Union
from pathlib import PurePath, Path
import py4cytoscape as p4c
from py4cytoscape import gen_node_color_map
from py4cytoscape import gen_edge_arrow_map
import os
import docker

from src.util import hash_filename

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

    






def viz_cytoscape_local(file: Union[str, PurePath], directed=False) -> None:
    suid = p4c.networks.import_network_from_tabular_file(
        file=file,
        column_type_list="s,t,x",
        delimiters=" "
    )
    p4c.networks.rename_network(file, network=suid)

    # if directed:
    #     p4c.set_visual_style("spras-directed", network=suid)
    # else:
    #     p4c.set_visual_style("default", network=suid)


if __name__ == '__main__':
    # run_cytoscape_container(['1', '2'])
    filename = 'output/egfr'
    hash1 = hash_filename(filename=filename)
    print(hash1)
    hash2 = hash_filename(filename=filename)
    print(hash2)




