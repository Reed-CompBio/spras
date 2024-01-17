from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.dataset import Dataset
from spras.interactome import reinsert_direction_col_undirected
from spras.prm import PRM
from spras.util import add_rank_column

__all__ = ['OmicsIntegrator2']

"""
Omics Integrator 2 will construct a fully undirected graph from the provided input file
- in the algorithm, it uses nx.Graph() objects, which are undirected
- uses the pcst_fast solver which supports undirected graphs

Expected raw input format:
Interactor1   Interactor2   Weight
- the expected raw input file should have node pairs in the 1st and 2nd columns, with a weight in the 3rd column
- it can include repeated and bidirectional edges
"""
class OmicsIntegrator2(PRM):
    required_inputs = ['prizes', 'edges']

    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files.
        Automatically converts edge weights to edge costs.
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in OmicsIntegrator2.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            # NODEID is always included in the node table
            node_df = data.request_node_columns(['prize'])
        elif data.contains_node_columns(['sources', 'targets']):
            # If there aren't prizes but are sources and targets, make prizes based on them
            node_df = data.request_node_columns(['sources', 'targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            raise ValueError("Omics Integrator 2 requires node prizes or sources and targets")

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

    # TODO add parameter validation
    # TODO add reasonable default values
    # TODO document required arguments
    @staticmethod
    def run(edges=None, prizes=None, output_file=None, w=None, b=None, g=None, noise=None, noisy_edges=None,
            random_terminals=None, dummy_mode=None, seed=None, container_framework="docker"):
        """
        Run Omics Integrator 2 in the Docker image with the provided parameters.
        Only the .tsv output file is retained and then renamed.
        All other output files are deleted.
        @param output_file: the name of the output file, which will overwrite any existing file with this name
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        if edges is None or prizes is None or output_file is None:
            raise ValueError('Required Omics Integrator 2 arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, edge_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        bind_path, prize_file = prepare_volume(prizes, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        # Omics Integrator 2 requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(out_dir, work_dir)
        volumes.append(bind_path)

        command = ['OmicsIntegrator', '-e', edge_file, '-p', prize_file,
                   '-o', mapped_out_dir, '--filename', 'oi2']

        # Add optional arguments
        if w is not None:
            command.extend(['-w', str(w)])
        if b is not None:
            command.extend(['-b', str(b)])
        if g is not None:
            command.extend(['-g', str(g)])
        if noise is not None:
            command.extend(['-noise', str(noise)])
        if noisy_edges is not None:
            command.extend(['--noisy_edges', str(noisy_edges)])
        if random_terminals is not None:
            command.extend(['--random_terminals', str(random_terminals)])
        if dummy_mode is not None:
            # This argument does not follow the other naming conventions
            command.extend(['--dummyMode', str(dummy_mode)])
        if seed is not None:
            command.extend(['--seed', str(seed)])

        print('Running Omics Integrator 2 with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "omics-integrator-2:v2"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

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
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # Omicsintegrator2 returns a single line file if no network is found
        num_lines = sum(1 for line in open(raw_pathway_file))
        if num_lines < 2:
            with open(standardized_pathway_file, 'w'):
                pass
            return
        df = pd.read_csv(raw_pathway_file, sep='\t')
        df = df[df['in_solution'] == True]  # Check whether this column can be empty before revising this line
        df = df.take([0, 1], axis=1)
        df = add_rank_column(df)
        df = reinsert_direction_col_undirected(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
