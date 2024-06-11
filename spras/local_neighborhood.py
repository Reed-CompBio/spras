import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_undirected,
)
from spras.util import add_rank_column
from spras.prm import PRM

__all__ = ['LocalNeighborhood']

class LocalNeighborhood(PRM):
    required_inputs = ["network", "nodes"]

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: dictionary where key is input type, and value is a path to a file
        @return:
        """
        print('generating inputs!!')
        # Check if filename
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # Select nodes that have sources, targets, prizes, or are active
        if data.contains_node_columns(['sources','targets','prize']):
            node_df = data.request_node_columns(['sources','targets','prize'])

        else:
            raise ValueError("LocalNeighborhood requires nore prizes or sources and targets")

        # LocalNeighborhood already gives warnings
        node_df.to_csv(filename_map['nodes'],
                        #sep='\t', 
                        index = False, 
                        columns=['NODEID'],
                        header=False)

        # Get network file
        edges_df = data.get_interactome()

        # Rename Direction column
        edges_df.to_csv(filename_map['network'],
                        sep='|',
                        index=False,
                        columns=['Interactor1','Interactor2'],
                        header=False)
        return None

    @staticmethod
    def run(nodes=None, network=None, output_file=None, container_framework="docker"):
        '''
        Method to running LocalNeighborhood correctly
        @param nodes:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_file: path to the output pathway file (required)
        '''
        print('Running!!!')
        if not nodes or not network or not output_file:
            raise ValueError('Required LocalNeighborhood arguments are missing')

        work_dir = '/spras'

        volumes = list()

        bind_path, node_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # LocalNeighborhood does not provide an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # LocalNeighborhood requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        command = ['python',
                   '/LocalNeighborhood/local_neighborhood.py',
                   '--network', network_file,
                   '--nodes', node_file,
                   '--output', mapped_out_prefix]

        print('Running LocalNeighborhood with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "local-neighborhood"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        # Currently LocalNeighborhood only writes one output file so we do not need to delete others
        output_edges = Path(out_dir, 'out')
        output_edges.rename(output_file)
        return None

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        '''
        Method for standardizing output data
        @raw_pathway_file: raw output from LocalNeighborhood
        @standardized_pathway_file: universal output, for use in Pandas analysis
        '''
        print('Parsing outputs!!')
        df = pd.read_csv(raw_pathway_file, 
            sep='|',
            header=None
            )

        # Add extra data to not annoy the SNAKEFILE
        df = add_rank_column(df)
        df = reinsert_direction_col_undirected(df)

        df.to_csv(standardized_pathway_file, 
                    header=None, 
                    index=False, 
                    sep='\t')
        return None
