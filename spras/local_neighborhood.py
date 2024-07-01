from spras.prm import PRM
from pathlib import Path
from spras.containers import prepare_volume, run_container
from spras.util import add_rank_column
import pandas as pd
from spras.interactome import reinsert_direction_col_undirected

__all__ = ['LocalNeighborhood']


class LocalNeighborhood(PRM):
    required_inputs = ['network', 'nodeinputs']

    @staticmethod
    def generate_inputs(data, filename_map):
        # both edge list and prizes
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        # print(filename_map)
        # print(data)
    
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        node_df = None

        if data.contains_node_columns('prize'):
            node_df = data.request_node_columns(['prize'])
        elif data.contains_node_columns(['active', 'sources', 'targets']):
            node_df = data.request_node_columns(['active', 'sources', 'targets'])
            node_df['prize'] = 0.0  # Initialize 'prize' column
            node_df.loc[node_df['active'] == True, 'prize'] = 1.0
            node_df.loc[node_df['sources'] == True, 'prize'] = 1.0
            node_df.loc[node_df['targets'] == True, 'prize'] = 1.0
        else:
            raise ValueError("Local Neighborhood requires node prizes or sources and targets")

        print(node_df) 
        
        node_df.to_csv(filename_map['nodetypes'],sep='\t',index=False,columns=['NODEID'],header=False)

        edges_df = data.get_interactome()

        print(edges_df)

        edges_df.to_csv(filename_map['network'],sep='|',index=False,
                        columns=['Interactor1','Interactor2'],
                        header=False)


    @staticmethod
    def run(nodeinputs=None, network=None, output_file=None, container_framework="docker"):
        """
        Run PathLinker with Docker
        @param nodeinputs:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_file: path to the output pathway file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        # Add additional parameter validation
        # Could consider setting the default here instead
        if not nodeinputs or not network or not output_file:
            raise ValueError('Required Local Neighborhood arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, node_file = prepare_volume(nodeinputs, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, mapped_out_file = prepare_volume(output_file, work_dir)
        volumes.append(bind_path)
        # mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        # print(mapped_out_prefix)
        command = ['python',
                   '/LocalNeighborhood/local_neighborhood.py',
                   '--network', network_file,
                   '--nodes', node_file,
                   '--output', mapped_out_file]

        print('Running Local Neighborhood with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "local-neighborhood" 
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        # We may not know the value of k that was used
        # output_edges = Path(next(out_dir.glob('out*-ranked-edges.txt')))
        # output_edges.rename(output_file)


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        try:
            df = pd.read_csv(raw_pathway_file, sep='|', header=None)
        except pd.errors.EmptyDataError:
            with open(standardized_pathway_file, 'w'):
                pass
            return
        # df.columns = ["vertex1", "vertex2", "1"]
        df = add_rank_column(df)
        df = reinsert_direction_col_undirected(df)
        df.to_csv(standardized_pathway_file, index=False,header=False, sep='\t')

