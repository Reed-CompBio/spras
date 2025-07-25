import warnings
from pathlib import Path

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_undirected_to_directed,
    has_direction,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['AllPairs']


class AllPairs(PRM):
    required_inputs = ['nodetypes', 'network', 'directed_flag']
    dois = []

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in AllPairs.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Get sources and targets for node input file
        # Borrowed code from pathlinker.py
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            raise ValueError("All Pairs Shortest Paths requires sources and targets")

        both_series = sources_targets.sources & sources_targets.targets
        for _index, row in sources_targets[both_series].iterrows():
            warn_msg = row.NODEID + " has been labeled as both a source and a target."
            warnings.warn(warn_msg, stacklevel=2)

        # Create nodetype file
        input_df = sources_targets[[Dataset.NODE_ID]].copy()
        input_df.columns = ["#Node"]
        input_df.loc[sources_targets["sources"] == True, "Node type"] = "source"
        input_df.loc[sources_targets["targets"] == True, "Node type"] = "target"

        input_df.to_csv(filename_map["nodetypes"], sep="\t", index=False, columns=["#Node", "Node type"])

        # Create network file
        edges_df = data.get_interactome()

        if edges_df is None:
            raise ValueError("Dataset does not have an interactome.")

        # Since APSP doesn't use the directed/undirected column because of a lack of support for mixed graphs (in NetworkX),
        # this function dynamically detects the usage of directed edges in user input
        # and, if the graph has a directed edge, it switches the entire graph to use directed edges, with a dummy file used to
        # signal to `run` that the graph is directed.
        if has_direction(edges_df):
            edges_df = convert_undirected_to_directed(edges_df)
            # we write to a 'directed_flag.txt' file to say that this is directed
            Path(filename_map['directed_flag']).write_text("true")
        else:
            Path(filename_map['directed_flag']).write_text("false")

        # This is pretty memory intensive. We might want to keep the interactome centralized.
        edges_df.to_csv(filename_map["network"], sep="\t", index=False,
                                      columns=["Interactor1", "Interactor2", "Weight"],
                                      header=["#Interactor1", "Interactor2", "Weight"])

    @staticmethod
    def run(nodetypes=None, network=None, directed_flag=None, output_file=None, container_framework="docker"):
        """
        Run All Pairs Shortest Paths with Docker
        @param nodetypes: input node types with sources and targets (required)
        @param network: input network file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        @param output_file: path to the output pathway file (required)
        """
        if not nodetypes or not network or not output_file or not directed_flag:
            raise ValueError('Required All Pairs Shortest Paths arguments are missing')

        work_dir = '/apsp'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(nodetypes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir)
        volumes.append(bind_path)

        command = ['python',
                   '/AllPairs/all-pairs-shortest-paths.py',
                   '--network', network_file,
                   '--nodes', node_file,
                   '--output', mapped_out_file]
        if Path(directed_flag).read_text().strip() == "true":
            command.append("--directed")

        container_suffix = "allpairs:v4"
        run_container_and_log(
            'All Pairs Shortest Paths',
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
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=None)
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_undirected(df)
            df.columns = ['Node1', 'Node2', 'Rank', 'Direction']
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
