from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container_and_log
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['MinCostFlow', 'MinCostFlowParams']

class MinCostFlowParams(BaseModel):
    flow: Optional[int] = None
    "amount of flow going through the graph"

    capacity: Optional[int] = None
    "amount of capacity allowed on each edge"

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

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
class MinCostFlow(PRM[MinCostFlowParams]):
    required_inputs = ['sources', 'targets', 'edges']
    # NOTE: This is the DOI for the ResponseNet paper.
    # This version of MinCostFlow is inspired by the ResponseNet paper, but does not have
    # its own referenceable DOI.
    dois = ["10.1038/ng.337"]

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type. Associated files will be written with:
        - sources: list of sources
        - targets: list of targets
        - edges: list of edges
        """

        MinCostFlow.validate_required_inputs(filename_map)

        # will take the sources and write them to files, and repeats with targets
        for node_type in ['sources', 'targets']:
            nodes = data.get_node_columns([node_type])
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
    def run(inputs, output_file, args=None, container_settings=None, timeout=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        if not args: args = MinCostFlowParams()
        MinCostFlow.validate_required_run_args(inputs)

        # the data files will be mapped within this directory within the container
        work_dir = '/mincostflow'

        # the tuple is for mapping the sources, targets, edges, and output
        volumes = list()

        bind_path, sources_file = prepare_volume(inputs["sources"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, targets_file = prepare_volume(inputs["targets"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume(inputs["edges"], work_dir, container_settings)
        volumes.append(bind_path)

        # Create a prefix for the output filename and ensure the directory exists
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir, container_settings)
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
        if args.flow is not None:
            command.extend(['--flow', str(args.flow)])
        if args.capacity is not None:
            command.extend(['--capacity', str(args.capacity)])

        # choosing to run in docker or singularity container
        container_suffix = "mincostflow"

        # constructs a docker run call
        run_container_and_log('MinCostFlow',
                             container_suffix,
                             command,
                             volumes,
                             work_dir,
                             out_dir,
                             container_settings,
                             timeout)

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
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert a predicted pathway into the universal format

        Although the algorithm constructs a directed network, the resulting network is treated as undirected.
        This is because the flow within the network doesn't imply causal relationships between nodes.
        The primary goal of the algorithm is node identification, not the identification of directional edges.

        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """

        df = raw_pathway_df(raw_pathway_file, sep='\t', header=None)
        if not df.empty:
            df = add_rank_column(df)
            # TODO update MinCostFlow version to support mixed graphs
            # Currently directed edges in the input will be converted to undirected edges in the output
            df = reinsert_direction_col_undirected(df)
            df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")

        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
