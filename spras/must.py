from pathlib import Path

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import duplicate_edges, raw_pathway_df

__all__ = ['MuST']


class MuST(PRM):
    required_inputs = ['network', 'seeds']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in MuST.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Create seeds file.
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            return False
        seeds_df = sources_targets[(sources_targets["sources"] == True) | (sources_targets["targets"] == True)]
        seeds_df = seeds_df.sort_values(by=[Dataset.NODE_ID], ascending=True, ignore_index=True)
        seeds_df.to_csv(filename_map['seeds'], index=False, columns=[Dataset.NODE_ID], header=None)

        # Create network file
        edges_df = data.get_interactome()
        edges_df = convert_undirected_to_directed(edges_df)
        edges_df.to_csv(filename_map["network"], columns=["Interactor1", "Interactor2", "Weight"], index=False, header=['Interactor1', 'Interactor2', 'weight'], sep='\t')

    @staticmethod
    def run(seeds=None, network=None, output_file=None, hub_penalty=None, trees=None, max_iterations=None, no_largest_cc=None, container_framework="docker"):
        """
        Run MuST with Docker
        @param seeds: input seeds with concatenated sources and targets (required)
        @param network: input network file (required)
        @param output_file: path to the output pathway file (required)
        @param hub_penalty: Specify hub penality between 0.0 and 1.0. If none is specified, there will be no hub penalty 
        @param max_iterations: The maximum number of iterations is defined as nrOfTrees + x. This is x, an integer between 0 and 20. Default: 10 
        @param no_largest_cc: Choose this option if you do not want to work with only the largest connected component 
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        # We don't use the flags multiple or trees, because we do not support multiple results yet.
        if not seeds or not network or not output_file:
            raise ValueError('Required MuST arguments are missing')

        work_dir = '/apsp'

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

        command = ['java',
                   '-jar',
                   '/MuST/MultiSteinerBackend.jar',
                   '--seed',
                   seeds_file,
                   '--network', network_file,
                   '--outedges', mapped_out_file,
                   # We can use the nodes file for visualization later,
                   # but it's not useful to us as of now.    
                   '--outnodes', '/MuST/nodes-artifact.txt']

        if hub_penalty is not None:
            command.extend(['--hubpenalty', str(hub_penalty)])
        if max_iterations is not None:
            command.extend(['--maxit', str(max_iterations)])
        if no_largest_cc is not None:
            command.extend(['--nolcc', str(no_largest_cc)])

        container_suffix = "must:latest"
        run_container_and_log('MuST',
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
        df = raw_pathway_df(raw_pathway_file, sep="\t", header=0)
        if not df.empty:
            df = reinsert_direction_col_directed(df)
            df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")

        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
