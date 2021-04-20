from src.PRM import PRM
import docker
from pathlib import Path
from src.util import prepare_path_docker


# TODO accept arguments with the parameters to write to the file
def write_conf(filename):
    """
    Write the configuration file for Omics Integrator 1
    See https://github.com/fraenkel-lab/OmicsIntegrator#required-inputs
    filename: the name of the configuration file to write
    """
    with open(filename, 'w') as f:
        f.write('w = 5\n')
        f.write('b = 1\n')
        f.write('D = 10\n')
        f.write('mu = 0\n')
        f.write('garnetBeta = 0.01\n')
        f.write('noise = 0.1\n')
        f.write('g = 0.001\n') # not the same as g in Omics Integrator 2
        f.write('r = 0\n')
        f.write('processes = 1\n')
        f.write('threads = 1\n')


class OmicsIntegrator1(PRM):

    def generate_inputs(self):
        print('Omics Integrator 1: generateInputs()')

    # TODO add parameter validation
    # TODO add additional parameters
    # TODO add reasonable default values
    @staticmethod
    def run(edge_input=None, prize_input=None, output_dir=None, out_label=None):
        """
        Run Omics Integrator 1 in the Docker image with the provided parameters.
        """
        if not edge_input or not prize_input or not output_dir:
            raise ValueError('Required Omics Integrator 1 arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        work_dir = Path(__file__).parent.parent.absolute()

        edge_file = Path(edge_input)
        prize_file = Path(prize_input)

        out_dir = Path(output_dir)
        # Omics Integrator 1 requires that the output directory exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        conf_file = 'oi1-configuration.txt'
        conf_file_abs = Path(work_dir, conf_file)
        write_conf(conf_file_abs)

        command = ['python', '/OmicsIntegrator/scripts/forest.py',
                   '--edge', edge_file.as_posix(),
                   '--prize', prize_file.as_posix(),
                   '--conf', conf_file,
                   '--msgpath', '/OmicsIntegrator/msgsteiner-1.3/msgsteiner',
                   '--outpath', out_dir.as_posix()]

        # Add optional arguments
        if out_label is not None:
            command.extend(['--outlabel', out_label])

        print('Running Omics Integrator 1 with arguments: {}'.format(' '.join(command)), flush=True)

        try:
            out = client.containers.run('agitter/omics-integrator-1',
                                  command,
                                  stderr=True,
                                  volumes={prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator1', 'mode': 'rw'}},
                                  working_dir='/OmicsIntegrator1')
            print(out.decode('utf-8'))
        finally:
            # Not sure whether this is needed
            client.close()
            conf_file_abs.unlink(missing_ok=True)

    def parse_output(self):
        print('Omics Integrator 1: parseOutput()')
