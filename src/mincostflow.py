from src.PRM import PRM
from pathlib import Path
from src.util import prepare_volume, run_container
import pandas as pd

__all__ = ['MinCostFlow']

class MinCostFlow (PRM):
    required_inputs = ['sources','targets','edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        
        # ensures the required input are within the filename_map 
        for input_type in MinCostFlow.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # will take the sources and write them to files, and repeats with targets 
        for node_type in ['sources', 'targets']:
            nodes = data.request_node_columns([node_type])
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files')
            
            nodes = nodes.loc[nodes[node_type]]

            # creates with the node type without headers 
            nodes.to_csv(filename_map[node_type], index=False, columns=['NODEID'], header=False)

        # create the network of edges 
        edges = data.get_interactome()
        
        # edges.insert(1, 'EdgeType', '(pp)') what does this do? do I need this?
        
        # creates the edges files that contains the head and tail nodes and the weights between them
        edges.to_csv(filename_map['edges'], sep='\t', index=False, columns=['Node1', 'Node2', 'Weight'], header=False)


