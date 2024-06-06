import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM

__all__ = ['LocalNeighborhood']

class LocalNeighborhood:
    required_inputs = ["network", "nodes"]

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map:
        @return:
        """
        
        # Check if filename
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            print("h")
        # Omics example
        if data.contains_node_columns('prize'):

            node_df = data.request_node_columns(['prize'])
        elif data.contains_node_columns('sources'):

            node_df = data.request_node_columns(['sources','targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0

        else:
            raise ValueError("LocalNeighborhood requires nore prizes or sources and targets")

        # LocalNeighborhood already gives warnings
        node_df.to_csv(filename_map['prizes'],sep='\t', index = False, columns=['NODEID','prize'],header=['name','prize'])

        # Get network file
        edges_df = data.get_interactome()

        # Rename Direction column
        edges_df.to_csv(filename_map['edges'],sep='\t',index=False,
                        columns=['Interactor1','Interactor2','Weight','Direction'],
                        header=['protein1','protein2','weight','directionality'])