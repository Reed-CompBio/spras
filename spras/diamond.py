from pathlib import Path

import networkx as nx

from spras.containers import prepare_volume, run_container
from spras.dataset import Dataset
from spras.interactome import convert_directed_to_undirected
from spras.prm import PRM
from spras.util import raw_pathway_df, df_nodes_from_networkx_graph, add_rank_column

__all__ = ['DIAMOnD']


class DIAMOnD(PRM):
    """
    DIAMOnD (https://doi.org/10.1371/journal.pcbi.1004120) is a disease module detection algorithm,
    which has been modified here, using sources and targets as seeds, to act as a pathway reconstruction algorithm.
    It does not account for node scores, and takes in undirected graphs as input.
    """
    required_inputs = ['seeds', 'network']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in DIAMOnD.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Create seeds file - we set the seeds as the sources and targets
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            return False
        seeds_df = sources_targets[(sources_targets["sources"] == True) | (sources_targets["targets"] == True)]
        seeds_df = seeds_df.sort_values(by=[Dataset.NODE_ID], ascending=True, ignore_index=True)
        seeds_df.to_csv(filename_map['seeds'], index=False, columns=[Dataset.NODE_ID], header=None)

        # Create network file
        edges_df = data.get_interactome()
        edges_df = convert_directed_to_undirected(edges_df)
        edges_df.to_csv(filename_map["network"], columns=["Interactor1", "Interactor2"], index=False, header=None, sep=',')

    @staticmethod
    def run(seeds=None, network=None, output_file=None, n=200, alpha=1, container_framework="docker"):
        """
        Run DIAMOnD with Docker
        @param seeds: input seeds (required)
        @param network: input network file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        @param n: the desired number of DIAMOnD genes to add.
        @param alpha: int representing weight of the seeds (default: 1)
        @param output_file: path to the output pathway file (required)
        """
        if not seeds or not network or not output_file:
            raise ValueError('DIAMOnD arguments are missing')

        # TODO we should dynamically calculate n.

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

        command = ['python',
                   '/DIAMOnD.py',
                   network_file,
                   seeds_file,
                   str(n),
                   str(alpha),
                   mapped_out_file]

        print('Running DIAMOnD with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "diamond:latest"
        out = run_container(
                            container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, original_dataset: Dataset):
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=0)
        if not df.empty:
            # preprocessing - drop [useful] p_hyper information, and rename columns to Rank and Node
            df = df.drop(columns=["p_hyper"])
            print(df)
            df.columns = ["Rank", "Node"]

            # TODO: we throw away rank information - we want this.
            # get induced subgraph of nodes
            nodes = df["Node"]
            G: nx.Graph | nx.DiGraph = original_dataset.interactome_to_networkx_undirected_graph().subgraph(nodes)

            # add default rank information
            nx.set_edge_attributes(G, 1, "rank")

            # convert back into a dataframe
            df = df_nodes_from_networkx_graph(G)
            df = add_rank_column(df)
        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
