from pathlib import Path

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import convert_directed_to_undirected
from spras.prm import PRM
from spras.secrets import gurobi

__all__ = ['NetMix2']

class NetMix2(PRM):
    required_inputs = ['network', 'scores']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: Dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in NetMix2.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            node_df = data.request_node_columns(['prize'])
        else:
            raise ValueError("Node prizes are required for NetMix2.")
        node_df.to_csv(filename_map['scores'], index=False, columns=['prize', 'NODEID'], header=False, sep='\t')

        edges_df = data.get_interactome()
        edges_df = convert_directed_to_undirected(edges_df)
        edges_df.to_csv(filename_map['network'], index=False, sep='\t', columns=['Interactor1', 'Interactor2'], header=False)

    @staticmethod
    def run(network=None, scores=None, output_file=None, delta=None, num_edges=None, density=None,
            container_framework="docker"):
        """
        Run NetMix2 with Docker
        @param network: input network file (required)
        @param scores: scores file (required)
        @param output_file: path to the output pathway file (required)
        @param delta: The similarity threshold (optional).
        @param num_edges: The number of edges in similarity threshold graph (optional). Default: 175000
        @param density: The minimum edge density of the altered subnetwork (optional). Default: 0.05
        """
        if not network or not scores or not output_file:
            raise ValueError('Required NetMix2 arguments are missing')

        gurobi_env = gurobi()
        if not gurobi_env:
            raise RuntimeError("gurobi license path is not present.\n" + \
                               "Make sure to specify the path in secrets.gurobi in `config.yaml`.")

        work_dir = '/spras'

        volumes = list()

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, scores_file = prepare_volume(scores, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'  # Use posix path inside the container

        command = ['python',
                   '/NetMix2/run_netmix2.py',
                   '-el',
                   network_file,
                   '-gs',
                   scores_file,
                   '-o', mapped_out_prefix + '/v-output.txt']

        # Add optional arguments
        if delta is not None:
            command.extend(['--delta', str(delta)])
        if num_edges is not None:
            command.extend(['--num_edges', str(num_edges)])
        if density is not None:
            command.extend(['--density', str(density)])

        container_suffix = "netmix2:v1"
        run_container_and_log('NetMix2',
                              container_framework,
                              container_suffix,
                              command,
                              volumes,
                              work_dir,
                              environment=gurobi_env)

        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        output_vertices = out_dir / 'out' / 'v-output.txt'
        output_vertices.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        with open(raw_pathway_file) as raw_pathway_file:
            [line.rstrip('\n') for line in raw_pathway_file if not str.isspace(line)]
