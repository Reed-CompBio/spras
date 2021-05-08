from src.PRM import PRM
import docker
from pathlib import Path
from src.util import prepare_path_docker

__all__ = ['OmicsIntegrator2']


class OmicsIntegrator2(PRM):
    required_inputs = ['prizes', 'edges']

    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in OmicsIntegrator2.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # TODO implement generate_inputs
        print('Omics Integrator 2: generateInputs()')

    # TODO add parameter validation
    # TODO add reasonable default values
    # TODO document required arguments
    @staticmethod
    def run(edges=None, prizes=None, output_file=None, w=None, b=None, g=None, noise=None, noisy_edges=None,
            random_terminals=None, dummy_mode=None, seed=None):
        """
        Run Omics Integrator 2 in the Docker image with the provided parameters.
        Only the .tsv output file is retained and then renamed.
        All other output files are deleted.
        @param output_file: the name of the output file, which will overwrite any existing file with this name
        """
        if not edges or not prizes or not output_file:
            raise ValueError('Required Omics Integrator 2 arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        work_dir = Path(__file__).parent.parent.absolute()

        edge_file = Path(edges)
        prize_file = Path(prizes)

        out_dir = Path(output_file).parent
        # Omics Integrator 2 requires that the output directory exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        command = ['OmicsIntegrator', '-e', edge_file.as_posix(), '-p', prize_file.as_posix(),
                   '-o', out_dir.as_posix(), '--filename', 'oi2']

        # Add optional arguments
        if w is not None:
            command.extend(['-w', str(w)])
        if b is not None:
            command.extend(['-b', str(b)])
        if g is not None:
            command.extend(['-g', str(g)])
        if noise is not None:
            command.extend(['-noise', str(noise)])
        if noisy_edges is not None:
            command.extend(['--noisy_edges', str(noisy_edges)])
        if random_terminals is not None:
            command.extend(['--random_terminals', str(random_terminals)])
        if dummy_mode is not None:
            # This argument does not follow the other naming conventions
            command.extend(['--dummyMode', str(dummy_mode)])
        if seed is not None:
            command.extend(['--seed', str(seed)])

        print('Running Omics Integrator 2 with arguments: {}'.format(' '.join(command)), flush=True)

        try:
            out = client.containers.run('reedcompbio/omics-integrator-2',
                                        command,
                                        stderr=True,
                                        volumes={
                                            prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator2', 'mode': 'rw'}},
                                        working_dir='/OmicsIntegrator2')
            print(out.decode('utf-8'))
        finally:
            # Not sure whether this is needed
            client.close()

        # TODO do we want to retain other output files?
        # Rename the primary output file to match the desired output filename
        Path(output_file).unlink(missing_ok=True)
        output_tsv = Path(out_dir, 'oi2.tsv')
        output_tsv.rename(output_file)
        # Remove the other output files
        for oi2_output in out_dir.glob('*.html'):
            oi2_output.unlink(missing_ok=True)

    def parse_output(self):
        print('Omics Integrator 2: parseOutput()')
