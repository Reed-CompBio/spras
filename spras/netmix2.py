from pathlib import Path

from spras.containers import prepare_volume, run_container
from spras.dataset import Dataset
from spras.prm import PRM

__all__ = ['NetMix2']

class NetMix2(PRM):
    required_inputs = ['edges', 'scores']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: Dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in NetMix2.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            node_df = data.request_node_columns(['prize'])
        else:
            raise ValueError("Node prizes are required for NetMix2.")
    
    @staticmethod
    def run(edges=None, scores=None, output_file=None, container_framework="docker"):
        if not edges or not scores or not output_file:
            raise ValueError('Required NetMix2 arguments are missing')

        work_dir = '/spras'

        volumes = list()

        bind_path, edges_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        bind_path, scores_file = prepare_volume(scores, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        command = ['python',
                   '/NetMix2/run_netmix2.py.py',
                   '-el',
                   edges_file,
                   '-gs',
                   scores_file,
                   '-o', mapped_out_prefix + '/v-output.txt']

        print('Running NetMix2 with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "netmix2"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        output_vertices = out_dir / 'out' / 'v-output.txt'
        output_vertices.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        pass
