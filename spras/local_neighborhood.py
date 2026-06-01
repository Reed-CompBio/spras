from pathlib import Path

from spras.config.container_schema import ProcessedContainerSettings
from spras.config.util import Empty
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import reinsert_direction_col_undirected
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['LocalNeighborhood']


class LocalNeighborhood(PRM[Empty]):
    required_inputs = ['network', 'nodes']
    dois = []

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Generate the Local Neighborhood input files from the SPRAS dataset.
        - nodes: list of relevant nodes (with prize, or active, or source, or target)
        - network: edges in the format <vertex1>|<vertex2>
        """
        LocalNeighborhood.validate_required_inputs(filename_map)

        candidate_columns = ['prize', 'active', 'sources', 'targets']
        existing_columns = [c for c in candidate_columns if c in data.node_table.columns]

        if not existing_columns:
            raise ValueError(
                "Dataset has none of: prize, active, sources, targets"
            )

        node_attrs = data.get_node_columns(existing_columns)

        mask = None
        for col in existing_columns:
            if col == 'prize':
                col_mask = node_attrs[col].notna()
            else:
                col_mask = node_attrs[col] == True  # noqa: E712
            mask = col_mask if mask is None else (mask | col_mask)

        selected_nodes = node_attrs[mask][[Dataset.NODE_ID]]
        selected_nodes.to_csv(filename_map['nodes'], sep='\t', index=False, header=False)

        edges_df = data.get_interactome()
        if edges_df is None:
            raise ValueError("Dataset does not have an interactome.")

        edges_df.to_csv(
            filename_map['network'],
            sep='|',
            index=False,
            header=False,
            columns=['Interactor1', 'Interactor2'],
        )

    @staticmethod
    def run(inputs, output_file, args=None, container_settings=None):
        """
        Run Local Neighborhood inside its Docker container.
        """
        if not container_settings:
            from spras.config import config as global_config
            container_settings = global_config.config.container_settings
        LocalNeighborhood.validate_required_run_args(inputs)

        work_dir = '/local_neighborhood'
        volumes = list()

        bind_path, network_file = prepare_volume(inputs['network'], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, nodes_file = prepare_volume(inputs['nodes'], work_dir, container_settings)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir, container_settings)
        volumes.append(bind_path)

        command = [
            'python',
            '/LocalNeighborhood/local_neighborhood_alg.py',
            '--network', network_file,
            '--nodes', nodes_file,
            '--output', mapped_out_file,
        ]

        container_suffix = "local-neighborhood"
        run_container_and_log(
            'Local Neighborhood',
            container_suffix,
            command,
            volumes,
            work_dir,
            out_dir,
            container_settings,
        )

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert Local Neighborhood output (A|B) into the SPRAS universal format
        (Node1\tNode2\tRank\tDirection).
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
