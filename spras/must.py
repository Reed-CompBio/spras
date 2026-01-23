from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import duplicate_edges, raw_pathway_df

__all__ = ['MuST', 'MuSTParams']

class MuSTParams(BaseModel):
    hub_penalty: Optional[float] = None
    """Specify hub penalty between 0.0 and 1.0. If none is specified, there will be no hub penalty"""

    max_iterations: int = 10
    """The maximum number of iterations is defined as nrOfTrees + x. This is x, an integer between 0 and 20."""

    no_largest_cc: bool = False
    """Choose this option if you do not want to work with only the largest connected component"""
    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

class MuST(PRM):
    required_inputs = ['network', 'seeds']
    dois = ["10.1038/s41467-020-17189-2", "10.1038/s41467-021-27138-2"]

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        - seeds: input seeds with concatenated sources and targets (required)
        - network: input network file (required)
        """
        MuST.validate_required_inputs(filename_map)

        # Create seeds file.
        sources_targets = data.get_node_columns(["sources", "targets"])
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
    def run(inputs, output_file, args=None, container_settings=None):
        # We don't use the flags multiple or trees, because we do not support multiple results yet.

        work_dir = '/apsp'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, seeds_file = prepare_volume(inputs["seeds"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(inputs["network"], work_dir, container_settings)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir, container_settings)
        volumes.append(bind_path)

        command = ['java',
                   '-jar',
                   '/MuST/MultiSteinerBackend.jar',
                   '--seed',
                   seeds_file,
                   '--network', network_file,
                   '--outedges', mapped_out_file,
                   '--maxit', str(args.max_iterations),
                   '--nolcc', str(args.no_largest_cc),
                   # We can use the nodes file for visualization later,
                   # but it's not useful to us as of now.
                   '--outnodes', '/MuST/nodes-artifact.txt']

        if args.hub_penalty is not None:
            command.extend(['--hubpenalty', str(args.hub_penalty)])

        container_suffix = "must:latest"
        run_container_and_log('MuST',
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
        df = raw_pathway_df(raw_pathway_file, sep="\t", header=0)
        if not df.empty:
            df = reinsert_direction_col_directed(df)
            df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")

        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
