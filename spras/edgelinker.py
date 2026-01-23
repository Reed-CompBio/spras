import warnings
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container, run_container_and_log
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['EdgeLinker', 'EdgeLinkerParams']

class EdgeLinkerParams(BaseModel):
    k: int = 100

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)


class EdgeLinker(PRM[EdgeLinkerParams]):
    required_inputs = ['network', 'sources', 'targets']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        - network: input network file (required)
        - sources: source nodes (required)
        - targets: target nodes (required)
        """
        for input_type in EdgeLinker.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Handle sources and targets (from MCF - TODO: deduplicate this?)
        for node_type in ['sources', 'targets']:
            nodes = data.get_node_columns([node_type])
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files.')
            nodes = nodes.loc[nodes[node_type]]
            nodes.to_csv(filename_map[node_type], index=False, columns=['NODEID'], header=False)

        # Create network file
        network = data.get_interactome()
        network = convert_undirected_to_directed(network)
        network.to_csv(filename_map['network'], sep='\t', index=False, columns=["Interactor1", "Interactor2", "Weight"],
                     header=False)

    @staticmethod
    def run(inputs, output_file, args=None, container_settings=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        if not args: args = EdgeLinkerParams()

        work_dir = '/EdgeLinker'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, network_file = prepare_volume(inputs["network"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, sources_file = prepare_volume(inputs["sources"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, targets_file = prepare_volume(inputs["targets"], work_dir, container_settings)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir, container_settings)
        volumes.append(bind_path)

        command = ['python',
                   '/EdgeLinker/edge_linker.py',
                   '--network', network_file,
                   '--sources', sources_file,
                   '--targets', targets_file,
                   '-k', str(args.k),
                   '--output', mapped_out_file]

        print('Running EdgeLinker with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "edgelinker:latest"
        run_container_and_log('EdgeLinker',
                              container_suffix,
                              command,
                              volumes,
                              work_dir,
                              out_dir,
                              container_settings)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=None)
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_directed(df)
            df.columns = ['Node1', 'Node2', 'Rank', 'Direction']
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
