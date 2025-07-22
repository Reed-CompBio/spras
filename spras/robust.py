from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_directed_to_undirected,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['ROBUST']


class ROBUST(PRM):
    """
    ROBUST as a Pathway Reconstruction Algorithm. This tries to connect a set of seed nodes (union of sources targets, internally
    referred to as terminal nodes) with prize-collecting sterner trees. This only takes in undirected input.

    ROBUST also allows passing in a custom study_bias file.
    """
    required_inputs = ['seeds', 'network', 'study_bias']
    dois = ["10.1093/bioinformatics/btad345"]

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in ROBUST.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Create seeds file - while ROBUST usually expects more seeds,
        # it will still try to construct PCSTs between all the seed nodes,
        # effectively reconstructing a PPI network.
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            return False
        seeds_df = sources_targets[(sources_targets["sources"] == True) | (sources_targets["targets"] == True)]
        seeds_df = seeds_df.sort_values(by=[Dataset.NODE_ID], ascending=True, ignore_index=True)
        seeds_df.to_csv(filename_map['seeds'], index=False, columns=[Dataset.NODE_ID], header=None)

        # Create network file
        edges_df = data.get_interactome()
        edges_df = convert_directed_to_undirected(edges_df)
        edges_df.to_csv(filename_map["network"], columns=["Interactor1", "Interactor2"], index=False, header=None, sep=' ')

        # Create study bias file
        if data.contains_node_columns('study_bias'):
            # NODEID is always included in the node table
            node_df = data.request_node_columns(['study_bias'])
            node_df = node_df.sort_values(by=[Dataset.NODE_ID], ascending=True, ignore_index=True)
            node_df.to_csv(filename_map['study_bias'], sep=',', index=False, columns=['NODEID', 'study_bias'], header=['gene_or_protein', 'study_bias_score'])
        else:
            # No study bias: we still create the file.
            Path(filename_map['study_bias']).touch()

    @staticmethod
    def run(seeds=None, network=None, study_bias=None, output_file=None, alpha=None, beta=None, n=None, tau=None, gamma=None, container_framework="docker"):
        """
        Run ROBUST with Docker
        @param seeds: input seeds with concatenated sources and targets (required)
        @param network: input network file (required)
        @param study_bias: input study_bias for each gene (required, can be empty)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        @param output_file: path to the output pathway file (required)
        @param alpha: initial fraction, in range [0, 1]. (optional) default: 0.25
        @param beta: reduction factor, float, in range [0, 1]. (optional) default: 0.90
        @param n: number of steiner trees. positive integer (optional) default: 30
        @param tau: threshold value, positive float. (optional) default: 0.1
        @param gamma: Hyper-parameter gamma used by bias-aware edge weights.
            This hyperparameter regulates to what extent the study bias data (scores) are being leveraged.
            float in range [0,1]. (optional) default: 1.00
        """
        if not seeds or not network or not output_file:
            raise ValueError('Required ROBUST arguments are missing')

        work_dir = '/robust'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, seeds_file = prepare_volume(seeds, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir)
        volumes.append(bind_path)

        command = ['python',
                   '/ROBUST/robust.py',
                   seeds_file,
                   mapped_out_file,
                   '--network', network_file]

        # Add optional arguments - we ignore study_bias if it's empty
        if Path(study_bias).read_text().strip() != "":
            bind_path, scores_file = prepare_volume(study_bias, work_dir)
            volumes.append(bind_path)
            command.extend(['--study-bias-scores', scores_file])
        else:
            command.extend(['--study-bias-scores', 'NONE'])
        if alpha is not None:
            command.extend(['--alpha', str(alpha)])
        if beta is not None:
            command.extend(['--beta', str(beta)])
        if n is not None:
            command.extend(['--n', str(n)])
        if tau is not None:
            command.extend(['--tau', str(tau)])
        if gamma is not None:
            command.extend(['--gamma', str(gamma)])

        container_suffix = "robust:latest"
        run_container_and_log('ROBUST',
                              container_framework,
                              container_suffix,
                              command,
                              volumes,
                              work_dir)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        df = raw_pathway_df(raw_pathway_file, sep="\\s+", header=None)
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_undirected(df)
            df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")

        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
