from src.PRM import PRM
from pathlib import Path
from src.util import prepare_volume, run_container
import pandas as pd

__all__ = ['MinCostFlow']

class MinCostFlow (PRM):
    required_inputs = ['sources','targets','edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        
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
        edges.to_csv(filename_map['edges'], sep='\t', index=False, columns=['Node1', 'Node2', 'Weight'], header=False)

    @staticmethod
    def run (sources = None, targets = None, edges= None, output = None, flow = None, capacity = None, singularity=False):
        
        # ensures that these parameters are required
        if not sources or not targets or not edges or not output:
            raise ValueError('Required PathLinker arguments are missing')

        # the data files will be mapped within this directory within the container
        work_dir = '/mincostflow'

        # the tuple is for mapping the sources, targets, edges, and output 
        volumes = list()

        # required arguments 

        bind_path, sources_file = prepare_volume(sources, work_dir) # sources_file = workingdirectory/joiefhowihfj/sources.txt (which is sources)
        volumes.append(bind_path)

        bind_path, targets_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume (edges, work_dir)
        volumes.append(bind_path)

        bind_path, output_file = prepare_volume(output, work_dir)
        volumes.append(bind_path)

        # makes the python command to run within in the container
        command = ['python',
                    'MinCostFlow/mincostflow.py',
                    sources_file,
                    targets_file,
                    edges_file,
                    output_file]

        #optional arguments (extend the command if available)

        if flow is not None:
            command.extend (['--flow', str(flow)])
        if capacity is not None:
            command.extend (['--capacity', str(capacity)])

        # choosing to run in docker or sigularity container
        container_framework = 'singularity' if singularity else 'docker'

        # constructs a docker run call 
        out = run_container(container_framework,
                            'ntalluri/mincostflow',
                            command, 
                            volumes, 
                            work_dir)

        # output of the executable script
        print(out)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        
        df = pd.read_csv(raw_pathway_file, sep = '\t')
        df.to_csv (standardized_pathway_file, header=False, index=False, sep='\t')