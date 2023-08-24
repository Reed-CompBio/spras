import warnings
from pathlib import Path

import pandas as pd

from src.prm import PRM
from src.util import prepare_volume, run_container

__all__ = ['LocalNeighborhood']

class LocalNeighborhood(PRM):
    required_inputs = ['nodes', 'network']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            #NODEID is always included in the node table
            node_df = data.request_node_columns(['prize'])
        elif data.contains_node_columns(['sources','targets']):
            #If there aren't prizes but are sources and targets, make prizes based on them
            node_df = data.request_node_columns(['sources','targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            raise ValueError("Local Neighborhood requires node prizes or sources and targets")

        #Local Neighborhood already gives warnings for strange prize values, so we won't here
        node_df.to_csv(filename_map['nodes'],
                       index=False,
                       columns=['NODEID'],
                       header=False)

        #For now we assume all input networks are undirected until we expand how edge tables work
        edges_df = data.get_interactome()
        edges_df.to_csv(filename_map['network'],
                        sep='|',
                        index=False,
                        columns=["Interactor1", "Interactor2"],
                        header=False
                        )


    # Skips parameter validation step
    @staticmethod
    def run(nodes=None, network=None, output_file=None, singularity=False):
        """
        Run PathLinker with Docker
        @param nodetypes:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_file: path to the output pathway file (required)
        @param k: path length (optional)
        @param singularity: if True, run using the Singularity container instead of the Docker container
        """
        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not nodes or not network or not output_file:
            raise ValueError('Required Local Neighborhood arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # Local Neighborhood provides an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # Local Neighborhood requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        command = ['python',
                   '/LocalNeighborhood/local_neighborhood.py',
                   '--network', network_file,
                   '--nodes', node_file,
                   '--output', mapped_out_prefix]

        print('Running Local Neighborhood with arguments: {}'.format(' '.join(command)), flush=True)

        # TODO consider making this a string in the config file instead of a Boolean
        container_framework = 'singularity' if singularity else 'docker'
        out = run_container(container_framework,
                            'oliverfanderson/local-neighborhood',
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        # Currently Local Neighborhood only writes one output file so we do not need to delete others
        output_edges = Path(out_dir, "out")
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # Questions: should there be a header/optional columns?
        # What about multiple raw_pathway_files
        df = pd.read_csv(raw_pathway_file, sep='|')
        df.insert(2, 'rank', 1)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
