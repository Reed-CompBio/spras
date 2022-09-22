from src.PRM import PRM
from pathlib import Path
from src.util import prepare_volume, run_container
import pandas as pd

__all__ = ['MinCostFlow']

class MinCostFlow (PRM):
    required_inputs = ['sources','targets','edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        
        for input_type in MinCostFlow.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        for node_type in ['sources', 'targets']:
            nodes = data.request_node_columns([node_type]) #has one column
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files')
            
            nodes = nodes.loc[nodes[node_type]] # take nodes one column data frame, call sources/ target series/ vector
            nodes.to_csv(filename_map[node_type], index=False, columns=['NODEID'], header=False)

        edges = data.get_interactome()
        edges.to_csv(filename_map['edges'], sep='\t', index=False, columns=['Interactor1', 'Interactor2', 'Weight'], header=False)


