#imports
from pathlib import Path
import pandas as pd
from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import add_rank_column


__all__ = ['LocalNeighborhood']


class LocalNeighborhood(PRM):
    required_inputs = ['network', 'nodes']

    @staticmethod
    def generate_inputs(data, filename_map):

        #Verifies that we have all of the input files we need
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        #Checks for valid cols, creates node_df by requesting cols that fit the criteria, slices the df for just the NODEID to create input file from
        if data.contains_node_columns(['prize', 'sources','targets','active']):
            node_df = data.request_node_columns(['prize', 'sources','targets','active'])
            node_df = node_df['NODEID']
            
        else:
            raise ValueError("Local Neighborhood requires nodes from sources, targets, actives or prizes")


        node_df.to_csv(filename_map['nodes'],sep='\t',index=False, header=False,columns=['NODEID'])    

        # Create network file
        edges = data.get_interactome()


        edges.to_csv(filename_map["network"],sep="|",index=False, header=False, columns=["Interactor1","Interactor2"],
                    )

    @staticmethod
    def run(nodes=None, network=None, output_file=None, container_framework="docker"):

        if not nodes or not network or not output_file:
            raise ValueError('Required LN arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, output_file = prepare_volume(output_file, work_dir)
        volumes.append(bind_path)

    
        #Debugging: Always use a forward slash instead of a backslash for file path, had a "\" here
        command = ['python',
                '/LocalNeighborhood/local_neighborhood.py',
                '--network', network_file,
                '--nodes', node_file,
                '--output', output_file]
                     


        print('Running LN with arguments: {}'.format(' '.join(command)), flush=True)

        #Debugging: Had to change suffix to match the name of Docker image, was missing "-"
        container_suffix = "local-neighborhood"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

     

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
     
        # sep='|', taking in the formatted output from LN, still | sep.
        df = pd.read_csv(raw_pathway_file, sep='|', header=None)
        df = add_rank_column(df)

        #All downstream output will require directionality added back, keep this line
        df = reinsert_direction_col_directed(df)

        #converting output to tab sep.
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
