import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM

__all__ = ['PathLinker']

"""
Pathlinker will construct a fully directed graph from the provided input file
- an edge is represented with a head and tail node, which represents the direction of the interation between two nodes
- uses networkx Digraph() object

Expected raw input format:
Interactor1   Interactor2   Weight
- the expected raw input file should have node pairs in the 1st and 2nd columns, with a weight in the 3rd column
- it can include repeated and bidirectional edges
"""
class PathLinker(PRM):
    required_inputs = ['nodetypes', 'network']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in PathLinker.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # Get sources and targets for node input file
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            return False
        both_series = sources_targets.sources & sources_targets.targets
        for _index, row in sources_targets[both_series].iterrows():
            warn_msg = row.NODEID + " has been labeled as both a source and a target."
            # Only use stacklevel 1 because this is due to the data not the code context
            warnings.warn(warn_msg, stacklevel=1)

        # Create nodetype file
        input_df = sources_targets[["NODEID"]].copy()
        input_df.columns = ["#Node"]
        input_df.loc[sources_targets["sources"] == True,"Node type"]="source"
        input_df.loc[sources_targets["targets"] == True,"Node type"]="target"

        input_df.to_csv(filename_map["nodetypes"],sep="\t",index=False,columns=["#Node","Node type"])

        # Create network file
        edges = data.get_interactome()

        # Format network file
        edges = convert_undirected_to_directed(edges)

        # This is pretty memory intensive. We might want to keep the interactome centralized.
        edges.to_csv(filename_map["network"],sep="\t",index=False,columns=["Interactor1","Interactor2","Weight"],
                     header=["#Interactor1","Interactor2","Weight"])
    #modify above to meet new file format req
    # Skips parameter validation step
    @staticmethod
    def run(nodetypes=None, network=None, output_file=None, k=None, container_framework="docker"):
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
        if not nodetypes or not network or not output_file:
            raise ValueError('Required PathLinker arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(nodetypes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # PathLinker does not provide an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # PathLinker requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        command = ['python',
                   '/PathLinker/run.py',
                   network_file,
                   node_file,
                   '--output', mapped_out_prefix]

        # Add optional argument
        if k is not None:
            command.extend(['-k', str(k)])

        print('Running PathLinker with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "pathlinker"
        out = run_container(container_framework,
                            container_suffix,
                            command,    
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        # We may not know the value of k that was used
        output_edges = Path(next(out_dir.glob('out*-ranked-edges.txt')))
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # What about multiple raw_pathway_files
        df = pd.read_csv(raw_pathway_file, sep='\t').take([0, 1, 2], axis=1)
        df = reinsert_direction_col_directed(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
