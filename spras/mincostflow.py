from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column

__all__ = ['MinCostFlow']

"""
MinCostFlow deals with fully directed graphs
- OR Tools MCF is designed for directed graphs
- when an edge (arc) is added, it has a source and target node, so flow is only allowed to move from source to the target
However, its the directionality it assigns to undirected edges via the flow assignments is not meaningful, so all
edges are currently undirected.

Expected raw input format:
Interactor1  Interactor2   Weight
- the expected raw input file should have node pairs in the 1st and 2nd columns, with the weight in the 3rd column
- it can include repeated and bidirectional edges
"""
class MinCostFlow (PRM):
    required_inputs = ['sources', 'targets', 'edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """

        # ensures the required input are within the filename_map
        for input_type in MinCostFlow.required_inputs:
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
        edges = data.get_interactome()

        # Format network edges
        edges = convert_undirected_to_directed(edges)

        # creates the edges files that contains the head and tail nodes and the weights after them
        edges.to_csv(filename_map['edges'], sep='\t', index=False, columns=["Interactor1", "Interactor2", "Weight"],
                     header=False)

    @staticmethod
    def run(sources=None, targets=None, edges=None, output_file=None, flow=None, capacity=None, container_framework="docker"):
        """
        Run min cost flow with Docker (or singularity)
        @param sources: input sources (required)
        @param targets: input targets (required)
        @param edges: input network file (required)
        @param output_file: output file name (required)
        @param flow: amount of flow going through the graph (optional)
        @param capacity: amount of capacity allowed on each edge (optional)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """

        # ensures that these parameters are required
        if not sources or not targets or not edges or not output_file:
            raise ValueError('Required MinCostFlow arguments are missing')

        # the data files will be mapped within this directory within the container
        work_dir = '/mincostflow'

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
                    '/MinCostFlow/minCostFlow.py',
                    '--sources_file', sources_file,
                    '--targets_file', targets_file,
                    '--edges_file', edges_file,
                    '--output', mapped_out_prefix]

        # Optional arguments (extend the command if available)
        if flow is not None:
            command.extend(['--flow', str(flow)])
        if capacity is not None:
            command.extend(['--capacity', str(capacity)])

        # choosing to run in docker or singularity container
        container_suffix = "mincostflow"

        # constructs a docker run call
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Check the output of the container
        out_dir_content = sorted(out_dir.glob('*.sif'))
        # Expected behavior is that one output network is created
        if len(out_dir_content) == 1:
            output_edges = out_dir_content[0]
            output_edges.rename(output_file)
        # Never expect to reach this case
        elif len(out_dir_content) > 1:
            raise RuntimeError('MinCostFlow produced multiple output networks')
        # This case occurs if there are errors such as too much flow
        else:
            raise RuntimeError('MinCostFlow did not produce an output network')

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
        # TODO update MinCostFlow version to support mixed graphs
        # Currently directed edges in the input will be converted to undirected edges in the output
        df = reinsert_direction_col_undirected(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')

