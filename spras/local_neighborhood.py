import warnings
from pathlib import Path
import pandas as pd

# Import necessary utilities from the spras package
from spras.containers import prepare_volume, run_container_and_log
from spras.interactome import reinsert_direction_col_undirected
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['LocalNeighborhood']

class LocalNeighborhood(PRM):
    """
    Local Neighborhood Algorithm Wrapper

    This class wraps the Local Neighborhood algorithm for use within the SPRAS framework.
    It handles generating the required input files (network and nodes) and running
    the algorithm inside a Docker container.

    Expected raw input network format (for --network):
    vertex1|vertex2
    - Each line represents an interaction. No header.
    - Assumed to be undirected or treated as such by the algorithm.

    Expected raw input nodes file format (for --nodes):
    NodeID
    - A simple list of node IDs, one per line. These are the query nodes for the algorithm.
    """
    required_inputs = ['network', 'nodes']

    @staticmethod
    def generate_inputs(data, filename_map):
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing in filename_map")

        node_df = data.node_table

        has_prize = node_df['prize'].notna() & (node_df['prize'] != '')
        is_active = node_df['active'] == True if 'active' in node_df.columns else pd.Series(False, index=node_df.index)
        is_source = node_df['sources'] == True if 'sources' in node_df.columns else pd.Series(False, index=node_df.index)
        is_target = node_df['targets'] == True if 'targets' in node_df.columns else pd.Series(False, index=node_df.index)

        selected_nodes_series = node_df.loc[has_prize | is_active | is_source | is_target, 'NODEID']

        if selected_nodes_series.empty:
            raise ValueError("No relevant nodes found to create the 'nodes' input file for Local Neighborhood.")

        nodes_filepath = filename_map["nodes"]
        with open(nodes_filepath, 'w') as f:
            for node_id in sorted(selected_nodes_series.unique().tolist()):
                f.write(f"{node_id}\n")

        interactome_df = data.get_interactome()
        if interactome_df is None or interactome_df.empty:
            raise ValueError("No interactome found to create the 'network' input file for Local Neighborhood.")

        network_content = interactome_df['Interactor1'].astype(str) + '|' + interactome_df['Interactor2'].astype(str)

        network_filepath = filename_map["network"]
        network_content.to_csv(network_filepath, sep='\n', index=False, header=False)


    @staticmethod
    def run(network=None, nodes=None, output_file=None, container_framework="docker"):
        if not network or not nodes or not output_file:
            raise ValueError("Required Local Neighborhood arguments (network, nodes, output_file) are missing.")

        work_dir = '/spras'

        volumes = []
        bind_path_network, mapped_network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path_network)

        bind_path_nodes, mapped_nodes_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path_nodes)

        out_dir = Path(output_file).parent
        bind_path_output_dir, mapped_output_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path_output_dir)

        command = [
            'python',
            '/app/LocalNeighborhood/local_neighborhood.py',
            '--network', mapped_network_file,
            '--nodes', mapped_nodes_file,
            '--output', Path(mapped_output_dir).joinpath(Path(output_file).name).as_posix()
        ]

        container_suffix = f"{LocalNeighborhood.name}:latest"

        run_container_and_log('Local Neighborhood',
                              container_framework,
                              container_suffix,
                              command,
                              volumes,
                              work_dir)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format.
        The Local Neighborhood output format is <vertex1>|<vertex2>.
        This function converts it to tab-separated Node1, Node2, Rank (1), Direction (U),
        and ensures no duplicate edges.

        @param raw_pathway_file: pathway file produced by an algorithm's run function.
        Expected format: vertex1|vertex2 per line, no header.
        @param standardized_pathway_file: the same pathway written in the universal format.
        """
        try:
            # Read the raw output file. Use read_csv with specific parameters
            # to ensure it's read as one column, then split.
            raw_df = pd.read_csv(raw_pathway_file, sep='\n', header=None, comment='#',
                                 skip_blank_lines=True, on_bad_lines='warn')

            if raw_df.empty:
                df = pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction'])
            else:
                # Split the single column by '|' into two new columns
                # n=1 limits to at most 1 split, creating 2 columns if '|' exists, otherwise 1.
                split_data = raw_df[0].str.split('|', expand=True, n=1)

                # Determine the number of columns after splitting
                num_split_cols = split_data.shape[1]

                if num_split_cols == 2:
                    df = pd.DataFrame({
                        'Node1': split_data[0],
                        'Node2': split_data[1]
                    })
                elif num_split_cols == 1:
                    # If only one column after split, assume it's Node1 and Node2 is empty
                    df = pd.DataFrame({
                        'Node1': split_data[0],
                        'Node2': '' # Assign empty string for Node2
                    })
                else:
                    raise ValueError(f"Unexpected number of columns after splitting raw pathway file: {num_split_cols}")

                # Add a 'Rank' column with value 1 
                df = add_rank_column(df)
                
                # Add a 'Direction' column with value 'U' for undirected edges
                df = reinsert_direction_col_undirected(df)
                
                # Ensure no duplicate edges in the output pathway
                df, has_duplicates = duplicate_edges(df)
                if has_duplicates:
                    print(f"Duplicate edges were removed from {raw_pathway_file}")

                # Ensure final columns order and names as required
                final_columns = ['Node1', 'Node2', 'Rank', 'Direction']
                df = df[final_columns]
            
            df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
            return True

        except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, KeyError, AttributeError, ValueError) as e:
            print(f"Error parsing Local Neighborhood output file {raw_pathway_file}: {e}", flush=True)
            pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction']).to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
            return False
