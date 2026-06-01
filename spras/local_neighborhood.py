import warnings
from pathlib import Path

from spras.config.container_schema import ProcessedContainerSettings
from spras.config.util import Empty
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_undirected_to_directed,
    has_direction,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df
__all__ = ['LocalNeighborhood']

class LocalNeighborhood(PRM[Empty]):
    required_inputs = ['network', 'nodes']
    dois = []
    
    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type. Associated files will be written with:
        - nodetypes: node types with sources and targets
        - network: network file containing edges and their weights
        - directed_flag: contains `true` if `network` is fully directed.
        """
        LocalNeighborhood.validate_required_inputs(filename_map)

        # Get sources and targets for node input file
        # Borrowed code from pathlinker.py
        sources_targets = data.get_node_columns(["sources", "targets"])

        both_series = sources_targets.sources & sources_targets.targets
        for _index, row in sources_targets[both_series].iterrows():
            warn_msg = row.NODEID + " has been labeled as both a source and a target."
            warnings.warn(warn_msg, stacklevel=2)

        # Create nodetype file
        input_df = sources_targets[[Dataset.NODE_ID]].copy()
        input_df.columns = ["#Node"]
        input_df.loc[sources_targets["sources"] == True, "Node type"] = "source"
        input_df.loc[sources_targets["targets"] == True, "Node type"] = "target"

        input_df.to_csv(filename_map["nodes"], sep="\t", index=False, columns=["#Node", "Node type"])

        # Create network file
        edges_df = data.get_interactome()

        if edges_df is None:
            raise ValueError("Dataset does not have an interactome.")

        edges_df.to_csv(
            filename_map['netowork'],
            sep='|',
            index=False,
            header=False,
            columns=['Interactor1','Interactor2'],
        )

        # Since APSP doesn't use the directed/undirected column because of a lack of support for mixed graphs (in NetworkX),
        # this function dynamically detects the usage of directed edges in user input
        # and, if the graph has a directed edge, it switches the entire graph to use directed edges, with a dummy file used to
        # signal to `run` that the graph is directed.
                                      
    @staticmethod
    def run(inputs, output_file, args=None, container_settings=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        LocalNeighborhood.validate_required_run_args(inputs)

        work_dir = '/local_neighborhood'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(inputs["networks"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(inputs["nodes"], work_dir, container_settings)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir, container_settings)
        volumes.append(bind_path)

        command = ['python',
                   '/LocalNeighborhood/local_neighborhood_alg.py',
                   '--network', network_file,
                   '--nodes', node_file,
                   '--output', mapped_out_file]
                   
        #if Path(inputs["directed_flag"]).read_text().strip() == "true":
            #command.append("--directed")

        container_suffix = "local-neighborhood"
        run_container_and_log(
            'Local Neighborhood Shortest Paths',
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
        df = raw_pathway_df(raw_pathway_file, sep='|', header=None)
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_undirected(df)
            df.columns = ['Node1', 'Node2', 'Rank', 'Direction']
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
