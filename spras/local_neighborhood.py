from pathlib import Path
import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.dataset import Dataset
from spras.interactome import reinsert_direction_col_undirected
from spras.prm import PRM
from spras.util import add_rank_column

__all__ = ['LocalNeighborhood']

class LocalNeighborhood(PRM):
    required_inputs = ['network', 'nodes']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: Dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")
        
        if data.contains_node_columns('prize'):
            node_df = data.request_node_columns(['prize'])
        else:
            raise ValueError("[LocalNeighborhood] node prizes are required.")
        node_df.to_csv(filename_map['nodes'], index=False, columns=['NODEID'], header=False)

        edges_df = data.get_interactome()
        edges_df.to_csv(filename_map['network'], index=False, sep="|", columns=['Interactor1', 'Interactor2'], header=False)

    @staticmethod
    def run(nodes=None, network=None, output_file=None, container_framework="docker"):
        if not nodes or not network or not output_file:
            raise ValueError('Required LocalNeighborhood arguments are missing!')
        
        work_dir = '/spras'

        volumes = list()
        
        bind_path, nodes_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        command = ['python',
                   '/LocalNeighborhood/local_neighborhood.py',
                   '--network',
                   network_file,
                   '--nodes',
                   nodes_file,
                   '--output', mapped_out_prefix + '/ln-output.txt']

        print('Running LocalNeighborhood with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "localneighborhood"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        output_vertices = out_dir.joinpath('out').joinpath('ln-output.txt')
        output_vertices.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        df = pd.read_csv(raw_pathway_file, sep="|", header=None)
        df = add_rank_column(df)
        df = reinsert_direction_col_undirected(df)
        df.to_csv(standardized_pathway_file, header=['Node1', 'Node2', 'Rank', 'Direction'], index=False, sep='\t')
