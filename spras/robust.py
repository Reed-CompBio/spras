import warnings
from pathlib import Path

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_directed_to_undirected,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['ROBUST']


class ROBUST(PRM):
    required_inputs = ['seeds', 'network', 'scores']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in ROBUST.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # TODO: Create seeds file
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            return False
    
        # Create network file
        edges = data.get_interactome()
        edges.to_csv(filename_map["network"], columns=["Interactor1", "Interactor2"], header=None, sep=' ')

        # Create scores file
        if data.contains_node_columns('prize'):
            # NODEID is always included in the node table
            node_df = data.request_node_columns(['prize'])
            node_df.to_csv(filename_map['scores'], sep=',', index=False, columns=['NODEID', 'prize'], header=['gene_or_protein', 'study_bias_score'])
        else:
            # TODO: fallback when there are no prizes
            raise ValueError("ROBUST doesn't require prizes, but we do not support no prizes yet.")

    @staticmethod
    def run(seeds=None, network=None, scores=None, output_file=None, container_framework="docker"):
        """
        Run All Pairs Shortest Paths with Docker
        @param seeds: input seeds with concatenated sources and targets (required)
        @param network: input network file (required)
        @param scores: input scores from genes (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        @param output_file: path to the output pathway file (required)
        """
        if not seeds or not network or not scores or not output_file:
            raise ValueError('Required All Pairs Shortest Paths arguments are missing')

        work_dir = '/apsp'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, seeds_file = prepare_volume(seeds, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, scores_file = prepare_volume(scores, work_dir)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir)
        volumes.append(bind_path)

        command = ['python',
                   '/ROBUST/robust.py',
                   seeds_file,
                   mapped_out_file,
                   '--network', network_file,
                   '--study-bias-scores', scores_file]

        print('Running ROBUST with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "robust:latest"
        out = run_container(container_framework,
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
        pass
