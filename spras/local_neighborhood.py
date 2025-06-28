from spras.containers import prepare_volume, run_container
from pathlib import Path

import pandas as pd 
from spras.util import duplicate_edges
import os 

# setting __all__ so SPRAS can automatically import this wrapper
__all__ = ["LocalNeighborhood"]

class LocalNeighborhood: 
    # tell Snakemake that this wrapper requires these inputs
    required_inputs = ['network', 'nodes']
    @staticmethod
    def generate_inputs(data, filename_map): 
        """
        Generate input files for LocalNeighborhood
        Expected: 
        - network: a file with interactome edges in '<node1>|<node2>' format
        - nodes: a file with nodes in the format "node_id"
        """

        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map: 
                raise ValueError(f"{input_type} filename is missing")
        
        # Determine which nodes to include 
        if data.contains_node_columns(['prize', 'active', 'sources', 'targets']):
            node_df = data.request_node_columns(['prize', 'active', 'sources', 'targets'])
        elif data.contains_node_columns(['active', 'sources', 'targets']):
            node_df = data.request_node_columns(['active', 'sources', 'targets'])
            node_df['prize'] = None 
        else: 
            raise ValueError("Dataset must contain at least one of the following node columns: 'prize', 'active', 'sources', 'targets'")

        # Determine relevant nodes to include 
        relevant_nodes = node_df[
            (node_df['prize'].notnull()) | 
            (node_df['active'] == True) | 
            (node_df['sources'] == True) | 
            (node_df['targets'] == True) 
        ][['NODEID']]

        # save relevant nodes to file 
        relevant_nodes.to_csv(filename_map['nodes'], sep='\t', index=False, header=False)

        # write the network edges to a file in <vertex1>|<vertex2> format
        edges_df = data.get_interactome()
        edges_df['edge'] = edges_df['Interactor1'] + '|' + edges_df['Interactor2']
        edges_df[['edge']].to_csv(filename_map['network'], index=False, header=False) 

    @staticmethod
    def run(nodes=None, network=None, output_file=None,  container_framework="docker"):
        """
        Run LocalNeighborhood with Docker 
        @param nodes: input node file 
        @param network: input network file 
        @param output_file: path to the output pathway file
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        # Catch if any inputs are missing 
        if not nodes or not network or not output_file: 
            raise ValueError("Missing required arguments for LocalNeighborhood")

        work_dir = "/spras"
        volumes = list() 

        # Bind input files
        bind_path, node_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # Ensure output file is a valid path 
        output_file_path = Path(output_file).resolve()
        output_parent = output_file_path.parent
        output_filename = output_file_path.name

        output_parent.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(output_parent), work_dir)
        volumes.append(bind_path)

        mapped_out_file = os.path.join(f"{mapped_out_dir}/{output_filename}")


        # Command to run LocalNeighborhood
        command = [
            'python', '/app/local_neighborhood.py', 
            '--network', network_file, 
            '--nodes', node_file, 
            '--output', mapped_out_file
        ]
        print('Running LocalNeighborhood with arguments: {}'.format(' '.join(command)), flush=True)
        container_suffix = "local-neighborhood:latest"
        out = run_container(
            container_framework,
            container_suffix,
            command,
            volumes,
            work_dir
        )
        print(out)



    @staticmethod
    def parse_output(raw_output_file, parsed_output_file): 
        """
        Convert LocalNeighborhood output into SPRAS format
        Input: file with lines in the format "A|B" 
        Output: tab-separated file with columns node1, node2, rank, direction
        """
        # Read the raw output file
        with open(raw_output_file, 'r') as f:
            lines = f.readlines()

        # split "A|B" into two columns
        edges_list = [line.strip().split('|') for line in lines if line.strip()]
        edge_df = pd.DataFrame(edges_list, columns=['Node1', 'Node2'])

        # Add rank and direction columns 
        edge_df['Rank'] = 1 # Placeholder for rank, can be modified later
        edge_df['Direction'] = "U" 

        # Remove duplicates and undirected edges 
        edge_df, _ = duplicate_edges(edge_df)

        # Save in SPRAS format 
        edge_df.to_csv(parsed_output_file, sep='\t', index=False, header=True)


