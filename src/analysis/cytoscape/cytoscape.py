from pathlib import PurePath
from typing import List, Union
from pathlib import PurePath, Path
import py4cytoscape as p4c
from py4cytoscape import gen_node_color_map
from py4cytoscape import gen_edge_arrow_map
import os

def run_cytoscape_container(pathways: List[Union[str, PurePath]]) -> None:
    '''
    1. take pathways and create volume mappings
    2. setup wrapper command 
    3. link cytoscape src at runtime
    
    '''

    command = []
    volumes = []


def viz_cytoscape_local(file: Union[str, PurePath], directed=False) -> None:
    print(directed)
    styles = Path("styles.xml")
    print(styles.parent.absolute())
    print(styles)
    p4c.import_visual_styles(os.path.abspath("styles.xml"))
    suid = p4c.networks.import_network_from_tabular_file(
        file=file,
        column_type_list="s,t,x",
        delimiters=" "
    )
    p4c.networks.rename_network(file, network=suid)
    if directed:
        p4c.set_visual_style("spras-directed", network=suid)
    else:
        p4c.set_visual_style("default", network=suid)




