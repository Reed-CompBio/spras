# need to define a new btb class and contain the following functions
# - generate_inputs
# - run
# - parse_output

import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
# from spras.interactome import (
#     convert_undirected_to_directed,
#     reinsert_direction_col_directed,
# )
# what type of directionality does btb support?

from spras.prm import PRM

__all__ = ['BowtieBuilder']

class BowtieBuilder(PRM):
    required_inputs = ['source', 'target', 'edges']

    #generate input taken from meo.py beacuse they have same input requirements
    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in BowtieBuilder.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")
        print("FILEMAP NAME: ", filename_map)
        print("DATA HEAD: ")
        print( data.node_table.head())
        print("DATA INTERACTOME: ")
        print(data.interactome.head())

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
                nodes.to_csv(filename_map["source"], sep= '\t', index=False, columns=['NODEID'], header=False)
                print("NODES: ")
                print(nodes)
            elif(node_type == "targets"):
                nodes.to_csv(filename_map["target"], sep= '\t', index=False, columns=['NODEID'], header=False)
                print("NODES: ")
                print(nodes)


        # Create network file
        edges = data.get_interactome()

        # Format network file
        #unsure if formating network file is needed
        # edges = add_directionality_constant(edges, 'EdgeType', '(pd)', '(pp)')

        edges.to_csv(filename_map['edges'], sep='\t', index=False, header=False)



        # Skips parameter validation step
    @staticmethod
    def run(source=None, target=None, edges=None, output_file=None, container_framework="docker"):
        """
        Run PathLinker with Docker
        @param nodetypes:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_file: path to the output pathway file (required)
        @param k: path length (optional)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not source or not target or not edges or not output_file:
            raise ValueError('Required BowtieBuilder arguments are missing')

        if not source.exists() or not target.exists() or not edges.exists():
            raise ValueError('Missing input file')

        work_dir = '/btb'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, source_file = prepare_volume(source, work_dir)
        volumes.append(bind_path)

        bind_path, target_file = prepare_volume(target, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        # PathLinker does not provide an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # PathLinker requires that the output directory exist
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


        print('Running BowtieBuilder with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "bowtiebuilder"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)
        print("Source file: ", source_file)
        print("target file: ", target_file)
        print("edges file: ", edges_file)
        print("mapped out dir: ", mapped_out_dir)
        print("mapped out prefix: ", mapped_out_prefix)





        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        # We may not know the value of k that was used
        # output_edges = Path(next(out_dir.glob('out*-ranked-edges.txt')))
        # output_edges.rename(output_file)


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # What about multiple raw_pathway_files
        print("PARSING OUTPUT BTB")
        df = pd.read_csv(raw_pathway_file, sep='\t').take([0, 1], axis=0)
        # df = reinsert_direction_col_directed(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
