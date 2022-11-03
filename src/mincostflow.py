from src.PRM import PRM
from pathlib import Path
from src.util import prepare_volume, run_container
import pandas as pd

__all__ = ['MinCostFlow']

class MinCostFlow (PRM):
    required_inputs = ['sources','targets','edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        
        # ensures the required input are within the filename_map 
        for input_type in MinCostFlow.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # will take the sources and write them to files, and repeats with targets 
        for node_type in ['sources', 'targets']:
            nodes = data.request_node_columns([node_type])
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files')
            # take nodes one column data frame, call sources/ target series/ vector
            nodes = nodes.loc[nodes[node_type]]
            # creates with the node type without headers 
            nodes.to_csv(filename_map[node_type], index=False, columns=['NODEID'], header=False)

        # create the network of edges 
        edges = data.get_interactome()
        
        # creates the edges files that contains the head and tail nodes and the weights after them
        edges.to_csv(filename_map['edges'], sep='\t',index=False, columns = ["Interactor1","Interactor2","Weight"], header=False)

    @staticmethod
    def run (sources = None, targets = None, edges= None, output_file = None, flow = None, capacity = None, singularity=False):
        """
        Run min cost flow with Docker (or singularity)
        @param sources:  input sources (required)
        @param targets: input targets (required)
        @param edges:  input network file (required)
        @param output_file: output file name (required)
        @param flow: amount of flow going through the graph (optional)
        @param capacity: amount of capacity allowed on each edge (optional)
        @param singularity: if True, run using the Singularity container instead of the Docker container
        """

        # ensures that these parameters are required
        if not sources or not targets or not edges or not output_file:
            raise ValueError('Required MinCostFlow arguments are missing')

        # the data files will be mapped within this directory within the container
        work_dir = '/mincostflow'

        # the tuple is for mapping the sources, targets, edges, and output 
        volumes = list()
 
        bind_path, sources_file = prepare_volume(sources, work_dir) # sources_file = workingdirectory/joiefhowihfj/sources.txt (which is sources)
        volumes.append(bind_path)

        bind_path, targets_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume (edges, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'
       
        # makes the python command to run within in the container
        command = ['python',
                    '/MinCostFlow/minCostFlow.py',
                    '--sources_file',sources_file,
                    '--targets_file',targets_file,
                    '--edges_file', edges_file,
                    '--output', mapped_out_prefix]
        
        #optional arguments (extend the command if available)
        if flow is not None:
            command.extend (['--flow', str(flow)])
        if capacity is not None:
            command.extend (['--capacity', str(capacity)])

        # choosing to run in docker or sigularity container
        container_framework = 'singularity' if singularity else 'docker'

        # constructs a docker run call 
        out = run_container(container_framework,
                            'ntalluri2/mincostflow',
                            command, 
                            volumes,
                            work_dir)
  
        # output of the executable script
        out_dir_content = sorted(out_dir.glob('*.sif'))

        print(type(out_dir_content))

        if len(out_dir_content) == 1: 
            output_edges = Path(next(out_dir.glob('*.sif')))
            output_edges.rename(output_file)
        elif len(out_dir_content) > 1: 
            raise RuntimeError('min cost flow produced multiple output networks')
        else: 
            raise RuntimeError('min cost flow did not produce an output network')

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        
        df = pd.read_csv(raw_pathway_file, sep = '\t', header=None)
        df.insert(2, 'Rank', 1) # adds in a rank column of 1's
        df.to_csv (standardized_pathway_file, header=False, index=False, sep=' ')