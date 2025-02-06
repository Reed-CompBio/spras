# need to define a new btb class and contain the following functions
# - generate_inputs
# - run
# - parse_output

import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column, raw_pathway_df


__all__ = ['BowTieBuilder']

class BowTieBuilder(PRM):
    required_inputs = ['sources', 'targets', 'edges']

    #generate input taken from meo.py beacuse they have same input requirements
    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in BowTieBuilder.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # Get sources and write to file, repeat for targets
        # Does not check whether a node is a source and a target
        for node_type in ['sources', 'targets']:
            nodes = data.request_node_columns([node_type])
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files')

            # TODO test whether this selection is needed, what values could the column contain that we would want to
            # include or exclude?
            nodes = nodes.loc[nodes[node_type]]
            if(node_type == "sources"):
                nodes.to_csv(filename_map["sources"], sep= '\t', index=False, columns=['NODEID'], header=False)
            elif(node_type == "targets"):
                nodes.to_csv(filename_map["targets"], sep= '\t', index=False, columns=['NODEID'], header=False)


        # Create network file
        edges = data.get_interactome()

        # Format into directed graph
        # edges = convert_undirected_to_directed(edges)

        edges.to_csv(filename_map["edges"], sep="\t", index=False,
                                      columns=["Interactor1", "Interactor2", "Weight"],
                                      header=False)



    # Skips parameter validation step
    @staticmethod
    def run(sources=None, targets=None, edges=None, output_file=None, container_framework="docker"):
        """
        Run BTB with Docker
        @param sources:  input source file (required)
        @param targets:  input target file (required)
        @param edges:    input edge file (required)
        @param output_file: path to the output pathway file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """

        # Tests for pytest (docker container also runs this) 
        # Testing out here avoids the trouble that container errors provide
        
        if not sources or not targets or not edges or not output_file:
            raise ValueError('Required BowTieBuilder arguments are missing')

        if not Path(sources).exists() or not Path(targets).exists() or not Path(edges).exists():
            raise ValueError('Missing input file')

        # Testing for btb index errors
        # It's a bit messy, but it works \_('_')_/
        with open(edges, 'r') as edge_file:
            try:
                for line in edge_file:
                    line = line.strip()
                    line = line.split('\t')
                    line = line[2]
                    
            except Exception as err:
                raise(err)

        work_dir = '/btb'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, source_file = prepare_volume(sources, work_dir)
        volumes.append(bind_path)

        bind_path, target_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/raw-pathway.txt'  # Use posix path inside the container

        command = ['python',
                   'btb.py',
                   '--edges',
                   edges_file,
                   '--sources',
                   source_file,
                   '--target',
                   target_file,
                   '--output',
                   mapped_out_prefix]
        # command = ['ls', '-R']


        print('Running BowTieBuilder with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "bowtiebuilder:v1"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)
        # Output is already written to raw-pathway.txt file


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # What about multiple raw_pathway_files
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=0)
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_undirected(df)
            df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
        df.to_csv(standardized_pathway_file, index=False, sep='\t', header=True)
