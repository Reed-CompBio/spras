import warnings
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import add_rank_column

__all__ = ['RWR']

"""
RWR will construct a directed graph from the provided input file
- an edge is represented with a head and tail node, which represents the direction of the interation between two nodes
- uses networkx Digraph() object

Expected raw input format:
Node1	Node2	Edge Flux	Weight	InNetwork	Type
- the expected raw input file should have node pairs in the 1st and 2nd columns, with a edge flux in the 3rd column, a weight in the 4th column, and a boolean in the 5th column to indicate if the edge/node is in the network
- the 'type' column should be 1 for edges, 2 for nodes, and 3 for pathways as we want to keep information about nodes, edges, and pathways.
- it can include repeated and bidirectional edges

Expected raw input format for prizes:
NODEID  prizes  Node type
- the expected raw input file should have node pairs in the 1st and 2nd columns, with a weight in the 3rd column
- it can include repeated and bidirectional edges
- if there are no prizes, the algorithm will assume that all nodes have a prize of 1.0
"""

class RWR(PRM):
    # we need edges (weighted), source set (with prizes), and target set (with prizes).
    required_inputs = ['edges', 'prizes']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """

        # ensures the required input are within the filename_map
        for input_type in RWR.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            if data.contains_node_columns('prize'):
                sources_targets = data.request_node_columns(['prize'])
                input_df = sources_targets[["NODEID"]].copy()
                input_df["Node type"] = "source"
            else:
                raise ValueError("No sources, targets, or prizes found in dataset")
        else:
            both_series = sources_targets.sources & sources_targets.targets
            for _index,row in sources_targets[both_series].iterrows():
                warn_msg = row.NODEID+" has been labeled as both a source and a target."
                # Only use stacklevel 1 because this is due to the data not the code context
                warnings.warn(warn_msg, stacklevel=1)

            #Create nodetype file
            input_df = sources_targets[["NODEID"]].copy()
            input_df.loc[sources_targets["sources"] == True,"Node type"]="source"
            input_df.loc[sources_targets["targets"] == True,"Node type"]="target"

            if data.contains_node_columns('prize'):
                node_df = data.request_node_columns(['prize'])
                input_df = pd.merge(input_df, node_df, on='NODEID')
            else:
                #If there aren't prizes but are sources and targets, make prizes based on them
                input_df['prize'] = 1.0

        input_df.to_csv(filename_map["prizes"],sep="\t",index=False,columns=["NODEID", "prize", "Node type"])

        # create the network of edges
        edges = data.get_interactome()

        edges = convert_undirected_to_directed(edges)

        # creates the edges files that contains the head and tail nodes and the weights after them
        edges.to_csv(filename_map['edges'], sep="\t", index=False, columns=["Interactor1","Interactor2","Weight"])


    # Skips parameter validation step
    @staticmethod
    def run(edges=None, prizes = None, output_file = None, single_source = None, df = None, w = None, f = None, threshold = None, container_framework="docker"):
        """
        Run RandomWalk with Docker
        @param edges:  input network file (required)
        @param prizes:  input node prizes with sources and targets (required)
        @param output_file: path to the output pathway file (required)
        @param df: damping factor for restarting (default 0.85) (optional)
        @param single_source: 1 for single source, 0 for source-target (default 1) (optional)
        @param w: lower bound to filter the edges based on the edge confidence (default 0.00) (optional)
        @param f: selection function (default 'min') (optional)
        @param threshold: threshold for constructing the final pathway (default 0.0001) (optional)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """

        if not edges or not prizes or not output_file:
            raise ValueError('Required RWR arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest) - data generated by Docker
        volumes = list()

        bind_path, edges_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        bind_path, prizes_file = prepare_volume(prizes, work_dir)
        volumes.append(bind_path)


        out_dir = Path(output_file).parent

        # RWR requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix= mapped_out_dir + '/out'  # Use posix path inside the container


        command = ['python',
                   '/RWR/random_walk.py',
                   '--edges_file', edges_file,
                   '--prizes_file', prizes_file,
                   '--output_file', mapped_out_prefix]

        if single_source is not None:
            command.extend(['--single_source', str(single_source)])
        if df is not None:
            command.extend(['--damping_factor', str(df)])
        if f is not None:
            command.extend(['--selection_function', str(f)])
        if w is not None:
            command.extend(['--w', str(w)])
        if threshold is not None:
            command.extend(['--threshold', str(threshold)])

        print('Running RWR with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "random-walk-with-restart"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        output = Path(out_dir, 'out')
        output.rename(output_file)


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """

        df = pd.read_csv(raw_pathway_file, sep="\t")

        # add a rank column to the dataframe
        df = add_rank_column(df)

        pathway_output_file = standardized_pathway_file
        edge_output_file = standardized_pathway_file.replace('.txt', '') + '_edges.txt'
        node_output_file = standardized_pathway_file.replace('.txt', '') + '_nodes.txt'

        # get all rows where type is 1
        df_edge = df.loc[df["Type"] == 1]

        # get rid of the placeholder column and output it to a file
        df_edge = df_edge.drop(columns=['Type'])
        df_edge = df_edge.drop(columns=['Rank'])
        df_edge.to_csv(edge_output_file, sep="\t", index=False, header=True)

        # locate the first place where placeholder is not Nan
        df_node = df.loc[df['Type'] == 2]
        # rename the header to Node, Pr, R_Pr, Final_Pr
        df_node = df_node.drop(columns=['Type'])
        df_node = df_node.drop(columns=['Rank'])
        df_node = df_node.rename(columns={'Node1': 'Node', 'Node2': 'Pr', 'Edge Flux': 'R_Pr', 'Weight': 'Final_Pr', 'InNetwork' : 'InNetwork'})
        df_node.to_csv(node_output_file, sep="\t", index=False, header=True)

        df_pathway = df.loc[df['Type'] == 3]
        df_pathway = df_pathway.drop(columns=['InNetwork'])
        df_pathway = df_pathway.drop(columns=['Type'])
        df_pathway = df_pathway.drop(columns=['Weight'])
        df_pathway = df_pathway.drop(columns=['Edge Flux'])

        df_pathway = reinsert_direction_col_directed(df_pathway)
        df_pathway.to_csv(pathway_output_file, sep="\t", index=False, header=False)
