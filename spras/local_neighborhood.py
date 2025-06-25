import warnings
from pathlib import Path
import pandas as pd

# Import necessary utilities from the spras package
from spras.containers import prepare_volume, run_container_and_log # Now using run_container_and_log
from spras.interactome import reinsert_direction_col_undirected # Needed for parse_output
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df # Needed for parse_output

__all__ = ['LocalNeighborhood']

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
class LocalNeighborhood(PRM):
    # Specify the required input file types for Snakemake.
    # Snakemake uses this list to ensure these files are present before the algorithm runs.
    required_inputs = ['network', 'nodes']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Accesses data from the dataset object and writes the required input files
        ('network' and 'nodes') for the Local Neighborhood algorithm.

        @param data: A dataset object from the SPRAS framework, containing interactome
                     and node information (sources/targets, prizes, active status).
        @param filename_map: A dictionary mapping required input types ('network', 'nodes')
                             to the specific filenames where they should be written.
        @return: True if inputs were successfully generated, False otherwise.
        """
        # Validate that all required input filenames are provided in the filename_map
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing in filename_map")

        # --- 1. Create the 'nodes' input file ---
        # The 'nodes' input for local_neighborhood.py is a list of relevant nodes
        # based on 'prize', 'active', 'sources', or 'targets'.
        node_df = data.node_table.copy() # Get a copy of the full node table

        # Identify nodes that have a non-empty prize
        has_prize = node_df['prize'].notna() & (node_df['prize'] != '') # Check for not NaN and not empty string
        # Identify nodes that are active, sources, or targets (Boolean attributes)
        is_active = node_df['active'] == True if 'active' in node_df.columns else pd.Series(False, index=node_df.index)
        is_source = node_df['sources'] == True if 'sources' in node_df.columns else pd.Series(False, index=node_df.index)
        is_target = node_df['targets'] == True if 'targets' in node_df.columns else pd.Series(False, index=node_df.index)

        # Combine all criteria to get the set of selected nodes
        selected_nodes_series = node_df.loc[has_prize | is_active | is_source | is_target, 'NODEID']

        if selected_nodes_series.empty:
            warnings.warn("No relevant nodes found (based on prize, active, source, or target status) "
                          "to create the 'nodes' input file for Local Neighborhood.", stacklevel=1)
            return False

        # Write the selected nodes to the designated 'nodes' file, one node ID per line
        nodes_filepath = filename_map["nodes"]
        with open(nodes_filepath, 'w') as f:
            for node_id in sorted(selected_nodes_series.unique().tolist()): # Get unique nodes and sort for reproducibility
                f.write(f"{node_id}\n")

        # --- 2. Create the 'network' input file ---
        # The 'network' input is all edges from the interactome, formatted as 'vertex1|vertex2', no header.
        interactome_df = data.get_interactome()
        if interactome_df is None or interactome_df.empty:
            warnings.warn("No interactome found in the dataset to create "
                          "the 'network' input file for Local Neighborhood.", stacklevel=1)
            return False

        # Ensure the interactome DataFrame has the required columns
        if not all(col in interactome_df.columns for col in ["Interactor1", "Interactor2"]):
            raise ValueError("Interactome DataFrame must contain 'Interactor1' and 'Interactor2' columns.")

        # Create the desired string format 'vertex1|vertex2'
        # Convert columns to string type before combining to avoid type issues if they are not already strings
        network_content = interactome_df['Interactor1'].astype(str) + '|' + interactome_df['Interactor2'].astype(str)

        # Write the formatted network content to the designated 'network' file, one string per line, no header.
        network_filepath = filename_map["network"]
        network_content.to_csv(network_filepath, sep='\n', index=False, header=False)

        return True # Indicate successful input generation


    @staticmethod
    def run(network=None, nodes=None, output_file=None, container_framework="docker"):
        """
        Executes the Local Neighborhood algorithm inside a Docker container.

        @param network: Path to the input network file on the host (required).
        @param nodes: Path to the input nodes file on the host (required).
        @param output_file: Path to the output file that the algorithm will write on the host (required).
        @param container_framework: The container runtime framework to use (e.g., "docker").
        """
        # Validate that all required arguments are provided for running the algorithm.
        if not network or not nodes or not output_file:
            raise ValueError("Required Local Neighborhood arguments (network, nodes, output_file) are missing.")

        # Define the working directory inside the Docker container.
        # This is the directory where host-mounted files will appear within the container.
        # This work_dir is often '/data' in SPRAS containers for mounted volumes.
        work_dir = '/spras'

        # Prepare a list to hold all volume mount configurations.
        volumes = []

        # Prepare volumes for the input 'network' file.
        bind_path_network, mapped_network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path_network)

        # Prepare volumes for the input 'nodes' file.
        bind_path_nodes, mapped_nodes_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path_nodes)

        # Prepare the volume for the output file's directory.
        # The Local Neighborhood algorithm will create the output file if its directory exists.
        # We prepare the *parent directory* of the output file for mounting.
        out_dir = Path(output_file).parent # Get the host's parent directory for the output file
        # It is not necessary to create the output directory on the host in advance;
        # prepare_volume handles ensuring its mountable path.
        bind_path_output_dir, mapped_output_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path_output_dir)

        # Construct the command array that will be executed inside the container.
        # This command explicitly calls the Python script located inside the Docker image
        # at '/app/LocalNeighborhood/local_neighborhood.py', passing the input and output arguments.
        command = [
            'python',
            '/app/LocalNeighborhood/local_neighborhood.py', # Absolute path to the script inside the Docker image
            '--network', mapped_network_file,  # Path to network file inside container
            '--nodes', mapped_nodes_file,      # Path to nodes file inside container
            # Construct the full path for the output file inside the container:
            # mapped_output_dir is the mounted parent directory, Path(output_file).name is just the filename.
            '--output', Path(mapped_output_dir).joinpath(Path(output_file).name).as_posix()
        ]

        # Define the Docker image name (suffix) for the Local Neighborhood algorithm.
        # This should match the tag used during the 'docker build' command (e.g., 'local-neighborhood' or 'your_username/local-neighborhood').
        container_suffix = "local-neighborhood" # Assuming this is your final image tag after building

        # Execute the Docker container using the helper function.
        # run_container_and_log is used to also log the container's output.
        run_container_and_log('Local Neighborhood', # Label for logging
                            container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir) # The container's effective working directory for bind mounts

        # No specific renaming or manipulation of the output file is needed here
        # as the algorithm is expected to write directly to 'output_file' due to volume mapping.

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
            # Read the raw output file, which is pipe-separated and has no header
            df = pd.read_csv(raw_pathway_file, sep='|', header=None, comment='#') # Added comment='#' in case of comments
            
            if not df.empty:
                # Assign initial column names based on the input format
                df.columns = ['Node1', 'Node2']

                # Add a 'Rank' column with value 1 (as per requirement)
                df = add_rank_column(df, rank_column_name='Rank', rank_value=1.0)
                
                # Add a 'Direction' column with value 'U' for undirected edges
                # reinsert_direction_col_undirected takes the DataFrame and ensures a 'Direction' column with 'U'
                df = reinsert_direction_col_undirected(df)
                
                # Ensure no duplicate edges in the output pathway
                df, has_duplicates = duplicate_edges(df)
                if has_duplicates:
                    print(f"Duplicate edges were removed from {raw_pathway_file}")

                # Ensure final columns order and names as required
                final_columns = ['Node1', 'Node2', 'Rank', 'Direction']
                df = df[final_columns] # Select and reorder columns
            else:
                # If the DataFrame is empty after reading, create an empty one with the correct columns
                df = pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction'])

            # Write the standardized pathway to the output file with header=True and tab separation
            df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')

        except Exception as e:
            print(f"Error parsing Local Neighborhood output file {raw_pathway_file}: {e}", flush=True)
            # Create an empty standardized file if parsing fails to prevent downstream errors
            pd.DataFrame(columns=['Node1', 'Node2', 'Rank', 'Direction']).to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
