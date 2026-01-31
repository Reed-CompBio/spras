from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict

from spras.config.container_schema import ProcessedContainerSettings
from spras.config.util import CaseInsensitiveEnum
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset, MissingDataError
from spras.interactome import reinsert_direction_col_undirected
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges

__all__ = ['DummyMode', 'OmicsIntegrator2', 'OmicsIntegrator2Params']

class DummyMode(CaseInsensitiveEnum):
    terminals = 'terminals'
    others = 'others'
    all = 'all'

class OmicsIntegrator2Params(BaseModel):
    w: float = 5
    "Omega: the weight of the edges connecting the dummy node to the nodes selected by dummyMode"

    b: float = 1
    "Beta: scaling factor of prizes"

    g: float = 3
    "Gamma: multiplicative edge penalty from degree of endpoints"

    noise: Optional[float] = None
    "Standard Deviation of the gaussian noise added to edges in Noisy Edges Randomizations."

    noisy_edges: Optional[int] = None
    "An integer specifying how many times to add noise to the given edge values and re-run."

    random_terminals: Optional[int] = None
    "An integer specifying how many times to apply your given prizes to random nodes in the interactome and re-run"

    dummy_mode: Optional[DummyMode] = None
    """
    Tells the program which nodes in the interactome to connect the dummy node to. (default: terminals)
        "terminals" = connect to all terminals
        "others" = connect to all nodes except for terminals
        "all" = connect to all nodes in the interactome.
    """

    seed: Optional[int] = None
    "The random seed to use for this run."

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

"""
Omics Integrator 2 will construct a fully undirected graph from the provided input file
- in the algorithm, it uses nx.Graph() objects, which are undirected
- uses the pcst_fast solver which supports undirected graphs

Expected raw input format:
Interactor1   Interactor2   Weight
- the expected raw input file should have node pairs in the 1st and 2nd columns, with a weight in the 3rd column
- it can include repeated and bidirectional edges
"""
class OmicsIntegrator2(PRM[OmicsIntegrator2Params]):
    required_inputs = ['prizes', 'edges']
    # OI2 does not have a specific paper. Instead, we link to the OI1 paper.
    dois = ["10.1371/journal.pcbi.1004879"]

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type. Associated files will be written with:
        - prizes: list of nodes associated with their prize
        - edges: list of edges associated with their cost (transformed from the original Dataset weights)
        """
        OmicsIntegrator2.validate_required_inputs(filename_map)

        if data.contains_node_columns('prize'):
            # NODEID is always included in the node table
            node_df = data.get_node_columns(['prize'])
        elif data.contains_node_columns(['sources', 'targets']):
            # If there aren't prizes but are sources and targets, make prizes based on them
            node_df = data.get_node_columns(['sources', 'targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            raise MissingDataError("(node prizes) or (sources and targets)")

        # Omics Integrator already gives warnings for strange prize values, so we won't here
        node_df.to_csv(filename_map['prizes'], sep='\t', index=False, columns=['NODEID', 'prize'], header=['name','prize'])

        # Create network file
        edges_df = data.get_interactome()

        # Format network file
        # edges_df = convert_directed_to_undirected(edges_df)
        # - technically this can be called but since we don't use the column and based on what the function does, it is not truly needed

        # We'll have to update this when we make iteractomes more proper, but for now
        # assume we always get a weight and turn it into a cost.
        # use the same approach as OmicsIntegrator2 by adding half the max cost as the base cost.
        # if everything is less than 1 assume that these are confidences and set the max to 1
        edges_df['cost'] = (max(edges_df['Weight'].max(), 1.0)*1.5) - edges_df['Weight']
        edges_df.to_csv(filename_map['edges'], sep='\t', index=False, columns=['Interactor1', 'Interactor2', 'cost'],
                        header=['protein1', 'protein2', 'cost'])

    # TODO add reasonable default values
    @staticmethod
    def run(inputs, output_file, args=None, container_settings=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        if not args: args = OmicsIntegrator2Params()
        OmicsIntegrator2.validate_required_run_args(inputs)

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, edge_file = prepare_volume(inputs["edges"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, prize_file = prepare_volume(inputs["prizes"], work_dir, container_settings)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        # Omics Integrator 2 requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(out_dir, work_dir, container_settings)
        volumes.append(bind_path)

        command = ['OmicsIntegrator', '-e', edge_file, '-p', prize_file,
                   '-o', mapped_out_dir, '--filename', 'oi2']

        # Add optional arguments
        if args.w is not None:
            command.extend(['-w', str(args.w)])
        if args.w is not None:
            command.extend(['-b', str(args.b)])
        if args.w is not None:
            command.extend(['-g', str(args.g)])
        if args.noise is not None:
            command.extend(['-noise', str(args.noise)])
        if args.noisy_edges is not None:
            command.extend(['--noisy_edges', str(args.noisy_edges)])
        if args.random_terminals is not None:
            command.extend(['--random_terminals', str(args.random_terminals)])
        if args.dummy_mode is not None:
            # This argument does not follow the other naming conventions
            command.extend(['--dummyMode', args.dummy_mode.value])
        if args.seed is not None:
            command.extend(['--seed', str(args.seed)])

        container_suffix = "omics-integrator-2:v3"
        run_container_and_log('Omics Integrator 2',
                             container_suffix,
                             command,
                             volumes,
                             work_dir,
                             out_dir,
                             container_settings,
                             network_disabled=True)

        # TODO do we want to retain other output files?
        # TODO if deleting other output files, write them all to a tmp directory and copy
        # the desired output file instead of using glob to delete files from the actual output directory
        # Rename the primary output file to match the desired output filename
        Path(output_file).unlink(missing_ok=True)
        output_tsv = Path(out_dir, 'oi2.tsv')
        output_tsv.rename(output_file)
        # Remove the other output files
        for oi2_output in out_dir.glob('*.html'):
            oi2_output.unlink(missing_ok=True)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # OmicsIntegrator2 returns a single line file if no network is found
        num_lines = sum(1 for line in open(raw_pathway_file))
        # OmicsIntegrator2 has corrupted output; list of correct column names
        sorted_correct_column_names = ['cost', 'in_solution', 'protein1', 'protein2'] # the order of edge attributes in the NetworkX graph is not guaranteed.

        if num_lines < 2:
            df = pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction'])
        else:
            df = pd.read_csv(raw_pathway_file, sep='\t', header=0)
            if sorted(df.columns) == sorted_correct_column_names: # if column header names are all correct
                df = df[df['in_solution'] == True]  # the 'in_solution' column exists when the forest is not empty.
                df = df.take([0, 1], axis=1) # the first two columns in the df will be 'protein1' and 'protein2', followed by the edge attributes.
                df = add_rank_column(df)
                df = reinsert_direction_col_undirected(df)
                df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            else: # corrupted data
                df = pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction'])

            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")

        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
