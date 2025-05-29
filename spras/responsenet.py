import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM

__all__ = ['ResponseNet']

"""
ResponseNet will construct a fully directed graph from the provided input file
- an edge is represented with a head and tail node, which represents the direction of the interation between two nodes
- uses networkx Digraph() object

Expected raw input format:
Interactor1   Interactor2   Weight
- the expected raw input file should have node pairs in the 1st and 2nd columns, with a weight in the 3rd column
- it can include bidirectional edges, but will only keep one copy of repeated edges
"""
class ResponseNet(PRM):
    required_inputs = ['sources', 'targets', 'edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """

        # ensures the required input are within the filename_map
        for input_type in ResponseNet.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # will take the sources and write them to files, and repeats with targets
        for node_type in ['sources', 'targets']:
            nodes = data.request_node_columns([node_type])
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files')
            # take nodes one column data frame, call sources/ target series
            nodes = nodes.loc[nodes[node_type]]
            # creates with the node type without headers
            nodes.to_csv(filename_map[node_type], index=False, columns=['NODEID'], header=False)

        # create the network of edges
        # responsenet should be recieving a directed graph
        edges = data.get_interactome()
        edges = convert_undirected_to_directed(edges)

        # creates the edges files that contains the head and tail nodes and the weights after them
        edges.to_csv(filename_map['edges'], sep='\t', index=False, columns=["Interactor1", "Interactor2", "Weight"],
                     header=False)

    @staticmethod
    def run(sources=None, targets=None, edges=None, output_file=None, gamma=10, _include_st=False, _verbose=False ,_output_log=False, container_framework="docker"):
        """
        Run ResponseNet with Docker (or singularity)
        @param sources: input sources (required)
        @param targets: input targets (required)
        @param edges: input network file (required)
        @param output_file: output file name (required)
        @param gamma: integer representing gamma (optional, default is 10)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        print("testing 2")

        # ensures that these parameters are required
        if not sources or not targets or not edges or not output_file:
            raise ValueError('Required ResponseNet arguments are missing')

        # the data files will be mapped within this directory within the container
        work_dir = '/ResponseNet'

        # the tuple is for mapping the sources, targets, edges, and output
        volumes = list()

        bind_path, sources_file = prepare_volume(sources, work_dir)
        volumes.append(bind_path)

        bind_path, targets_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        # Create a prefix for the output filename and ensure the directory exists
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'

        # Makes the Python command to run within in the container
        command = ['python',
                    'responsenet.py',
                    '--edges_file', edges_file,
                    '--sources_file', sources_file,
                    '--targets_file', targets_file,
                    '--output', mapped_out_prefix,
                    '--gamma', gamma]

        # add optional flags, value can be changed in config/config.yaml
        if _include_st:
            command.append('-st')
        if _verbose:
            command.append('-v')
        if _output_log:
            command.append('-o')

        # choosing to run in docker or singularity container
        container_suffix = "responsenet"

        #print(container_framework, container_suffix, command, volumes, work_dir, sep="\n")

        # constructs a docker run call
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

    # TODO: Make sure we get an output file and a log file for user inspection, see DOMINO


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format

        Although the algorithm constructs a directed network, the resulting network is treated as undirected.
        This is because the flow within the network doesn't imply causal relationships between nodes.
        The primary goal of the algorithm is node identification, not the identification of directional edges.

        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """

        df = pd.read_csv(raw_pathway_file, sep='\t', header=None)
        df = add_rank_column(df)
        # Currently directed edges in the input will be converted to undirected edges in the output
        df = reinsert_direction_col_directed(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')

