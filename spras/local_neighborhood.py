# imports ame all allpairs.py in the same directory on website 
from pathlib import Path, PurePosixPath
import pandas as pd
from spras.config.container_schema import ProcessedContainerSettings
from spras.config.util import Empty
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset, MissingDataError
from spras.interactome import reinsert_direction_col_undirected
from spras.util import add_rank_column, duplicate_edges
from spras.spras_logging import indent
import spras.prm


__all__ = ['LocalNeighborhood']

class LocalNeighborhood(spras.prm.PRM[Empty]): # type: ignore
    required_inputs = ["network", "nodes"]
    dois = []

    @staticmethod

    def generate_inputs(data: Dataset, filename_map):
        """
        Selected nodes should be any node in the dataset that has a prize set, any node that is active, 
        any node that is a source, or any node that is a target. As shown in the example dataset above, 
        "active", "sources", and "targets" are Boolean attributes.

        A "prize" is a term for a numeric score on a node in a network, so nodes that have non-empty prizes 
        are considered relevant nodes for the Local Neighborhood algorithm along with active nodes, sources, and targets. 
        The network should be all of the edges written in the format <vertex1>|<vertex2>
        """
        LocalNeighborhood.validate_required_inputs(filename_map) # type: ignore

         # get the nodes needed for the algorithem 
        node_table = data.node_table

        selected = (
            node_table['prize'].notna() |
            (node_table['active'] == True) |
            (node_table['sources'] == True) |
            (node_table['targets'] == True)
        ) # get the nodes that have prizes, are active, are sources, or are targets

        selected_nodes = node_table[selected]['NODEID']
        # Now we want to put all the information into a csv file or something simillar that allows us to read the data easier (i.e. df)
        if selected_nodes.empty:
            raise MissingDataError("(node prizes) or (active, sources, and targets)")

        # Write node IDs to the nodes file, one per line, no header
        selected_nodes.to_csv(filename_map['nodes'], index=False, header=False)

        # Get interactome edges and write in <vertex1>|<vertex2> format
        edges_df = data.get_interactome()
        edges_df['edge'] = edges_df['Interactor1'] + '|' + edges_df['Interactor2']
        edges_df[['edge']].to_csv(filename_map['network'], index=False, header=False)

        # Check the `dataset.py` file to see how the interactome edges are written to a file 
        # and make sure it is in the correct format for the algorithm.

        # Include a key-value pair in the algo_exp_file dictionary that links 
        # the specific algorithm to its expected network file.
        # Obtain the expected network file from the workflow, manually confirm it is correct, and save it
        algo_exp_file = {}
        for key in filename_map:
            if 'network'or 'node'in key:
                algo_exp_file[key] = filename_map[key] 
                return algo_exp_file

    @staticmethod
    
    def run(inputs, output_file, arg = None, container_settings=None):
        """
        The prepare_volume utility function is needed to prepare the network and nodes input files to be mounted
        and used inside the container. It is also used to prepare the path for the output file.
        The functionality of prepare_volume is similar to how you had to manually specify paths relative 
        to the containers file system when you interactive tested the container in Step 2. 

        A container is a separate file system, so you need to prepare the input files to be mounted inside the 
        container and specify the path for the output file to be created inside the container.
        """   
        if not container_settings: container_settings = ProcessedContainerSettings()
        LocalNeighborhood.validate_required_run_args(inputs)

        work_dir = '/data' # the working directory inside the container where the input files will be mounted and the output file will be created 

        volumes = list() # Each volume is a tuple (src, dest)

        # Prepare the input files to be mounted inside the container
        bind_path, node_file = prepare_volume(inputs['nodes'], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(inputs['network'], work_dir, container_settings) 
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        # Create output directory if it doesn't exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir, container_settings)
        volumes.append(bind_path)

        # Use PurePosixPath to ensure forward slashes for container paths
        output_filename = Path(output_file).name
        container_output_path = str(PurePosixPath(mapped_out_dir) / output_filename)
        
        cmd = ['python', 'local_neighborhood_alg.py',
            '--network', network_file,
            '--nodes', node_file,
            '--output', container_output_path]
        
        run_container_and_log(
            'Local Neighborhood',
            'local-neighborhood:v1',
            cmd,
            volumes,
            work_dir,
            out_dir,
            container_settings
        )
    
    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        The edges in the Local Neighborhood output have the same format as the input, <vertex1>|<vertex2>. 
        Convert these to be tab-separated vertex pairs followed by a tab 1 and tab U at the end of every line, which indicates all 
        edges have the same rank and are undirected.
        The parse_output function also ensures that there are no duplicate edges in the output pathway.
        Make sure header = True with column names: ['Node1', 'Node2', 'Rank', 'Direction'] when the file is created. 
        The output should have the format <vertex1> <vertex2> 1 U.
        """
        # use the output after running 'cmd' and sort that into a df w/ pandas 

        # The first thing I want to do is have the data here stored in variable(s) so I can use that to parse the output
        # putting it in the <vertex 1>|<vertex 2> format needed 
        # have to do something like df['Vertex_Combined'] = df['VertexA'].astype(str) + '|' + df['VertexB'].astype(str) after getting data - Google
        

        # Read raw output — edges in vertex1|vertex2 format
        edges = pd.read_csv(raw_pathway_file, header=None, names=['edge'])

        # Split the edge column into Node1 and Node2
        edges[['Node1', 'Node2']] = edges['edge'].str.split('|', expand=True)
        edges = edges.drop(columns=['edge'])

        # Add rank and direction columns
        edges = add_rank_column(edges)
        edges = reinsert_direction_col_undirected(edges)

        # Remove duplicate edges
        edges, has_duplicates = duplicate_edges(edges)
        if has_duplicates:
            print(f"Duplicate edges were removed from {raw_pathway_file}")

        # Write standardized output with header
        edges.to_csv(
            standardized_pathway_file,
            sep='\t',
            index=False,
            columns=['Node1', 'Node2', 'Rank', 'Direction'],
            header=True)

        print(edges.head())
        print(edges.columns)
        print(edges)
        print("test")


        pass 
    
print("it worked")
