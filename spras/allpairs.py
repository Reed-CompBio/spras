import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_directed_to_undirected,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM

__all__ = ['AllPairs']


class AllPairs(PRM):
    required_inputs = ['nodetypes', 'network']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in AllPairs.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Get sources and targets for node input file
        # Borrowed code from pathlinker.py
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            raise ValueError("All Pairs Shortest Paths requires sources and targets")

        both_series = sources_targets.sources & sources_targets.targets
        for _index, row in sources_targets[both_series].iterrows():
            warn_msg = row.NODEID + " has been labeled as both a source and a target."
            warnings.warn(warn_msg, stacklevel=2)

        # Create nodetype file
        input_df = sources_targets[["NODEID"]].copy()
        input_df.columns = ["#Node"]
        input_df.loc[sources_targets["sources"] == True, "Node type"] = "source"
        input_df.loc[sources_targets["targets"] == True, "Node type"] = "target"

        input_df.to_csv(filename_map["nodetypes"], sep="\t", index=False, columns=["#Node", "Node type"])

        # Create network file
        edges_df = data.get_interactome()

        # Format network file
        # edges_df = convert_directed_to_undirected(edges_df)
        # - technically this can be called but since we don't use the column and based on what the function does, it is not truly needed

        # This is pretty memory intensive. We might want to keep the interactome centralized.
        edges_df.to_csv(filename_map["network"], sep="\t", index=False,
                                      columns=["Interactor1", "Interactor2", "Weight"],
                                      header=["#Interactor1", "Interactor2", "Weight"])

    @staticmethod
    def run(nodetypes=None, network=None, output_file=None, container_framework="docker"):
        """
        Run All Pairs Shortest Paths with Docker
        @param nodetypes: input node types with sources and targets (required)
        @param network: input network file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        @param output_file: path to the output pathway file (required)
        """
        if not nodetypes or not network or not output_file:
            raise ValueError('Required All Pairs Shortest Paths arguments are missing')

        work_dir = '/apsp'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(nodetypes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir)
        volumes.append(bind_path)

        command = ['python',
                   '/AllPairs/all-pairs-shortest-paths.py',
                   '--network', network_file,
                   '--nodes', node_file,
                   '--output', mapped_out_file]

        print('Running All Pairs Shortest Paths with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "allpairs"

        out = run_container(
                            container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        df = pd.read_csv(raw_pathway_file, sep='\t', header=None)
        df['Rank'] = 1  # add a rank column of 1s since the edges are not ranked.
        df = reinsert_direction_col_undirected(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
