from src.PRM import PRM
import docker
from pathlib import Path
from src.util import prepare_path_docker


# TODO decide on default number of processes and threads
def write_conf(filename=Path('config.txt'), w=None, b=None, d=None, mu=None, noise=None, g=None, r=None):
    """
    Write the configuration file for Omics Integrator 1
    See https://github.com/fraenkel-lab/OmicsIntegrator#required-inputs
    filename: the name of the configuration file to write
    """
    if not w or not b or not d:
        raise ValueError('Required Omics Integrator 1 configuration file arguments are missing')

    with open(filename, 'w') as f:
        f.write(f'w = {w}\n')
        f.write(f'b = {b}\n')
        f.write(f'D = {d}\n')
        if mu is not None:
            f.write(f'mu = {mu}\n')
        # Not supported
        #f.write('garnetBeta = 0.01\n')
        if noise is not None:
            f.write(f'noise = {noise}\n')
        if g is not None:
            f.write(f'g = {g}\n') # not the same as g in Omics Integrator 2
        if r is not None:
            f.write(f'r = {r}\n')
        f.write('processes = 1\n')
        f.write('threads = 1\n')


class OmicsIntegrator1(PRM):

    def generate_inputs(self):
        print('Omics Integrator 1: generateInputs()')

    # TODO add parameter validation
    # TODO add support for knockout argument
    # TODO add reasonable default values
    @staticmethod
    def run(edge_input=None, prize_input=None, dummy_mode=None, mu_squared=None, exclude_terms=None,
            outpath=None, outlabel=None, noisy_edges=None, shuffled_prizes=None, random_terminals=None,
            seed=None, w=None, b=None, d=None, mu=None, noise=None, g=None, r=None):
        """
        Run Omics Integrator 1 in the Docker image with the provided parameters.
        Does not support the garnet, cyto30, knockout, cv, or cv-reps arguments.
        The configuration file is generated from the provided arguments.
        Does not support the garnetBeta, processes, or threads configuration file parameters.
        The msgpath is not required because msgsteiner is available in the Docker image.
        """
        if not edge_input or not prize_input or not outpath or not w or not b or not d:
            raise ValueError('Required Omics Integrator 1 arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        work_dir = Path(__file__).parent.parent.absolute()

        edge_file = Path(edge_input)
        prize_file = Path(prize_input)

        out_dir = Path(outpath)
        # Omics Integrator 1 requires that the output directory exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        conf_file = 'oi1-configuration.txt'
        conf_file_abs = Path(work_dir, conf_file)
        write_conf(conf_file_abs, w=w, b=b, d=d, mu=mu, noise=noise, g=g, r=r)

        command = ['python', '/OmicsIntegrator/scripts/forest.py',
                   '--edge', edge_file.as_posix(),
                   '--prize', prize_file.as_posix(),
                   '--conf', conf_file,
                   '--msgpath', '/OmicsIntegrator/msgsteiner-1.3/msgsteiner',
                   '--outpath', out_dir.as_posix()]

        # Add optional arguments
        if dummy_mode is not None:
            command.extend(['--dummyMode', str(dummy_mode)])
        if mu_squared is not None and mu_squared:
            command.extend(['--musquared'])
        if exclude_terms is not None and exclude_terms:
            command.extend(['--excludeTerms'])
        if outlabel is not None:
            command.extend(['--outlabel', str(outlabel)])
        if noisy_edges is not None:
            command.extend(['--noisyEdges', str(noisy_edges)])
        if shuffled_prizes is not None:
            command.extend(['--shuffledPrizes', str(shuffled_prizes)])
        if random_terminals is not None:
            command.extend(['--randomTerminals', str(random_terminals)])
        if seed is not None:
            command.extend(['--seed', str(seed)])

        print('Running Omics Integrator 1 with arguments: {}'.format(' '.join(command)), flush=True)

        try:
            out = client.containers.run('reedcompbio/omics-integrator-1',
                                  command,
                                  stderr=True,
                                  volumes={prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator1', 'mode': 'rw'}},
                                  working_dir='/OmicsIntegrator1')
            print(out.decode('utf-8'))
        finally:
            # Not sure whether this is needed
            client.close()
            conf_file_abs.unlink(missing_ok=True)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # I'm assuming from having read the documentation that we will be passing in optimalForest.sif
        # as raw_pathway_file, in which case the format should be edge1 interactiontype edge2.
        # if that assumption is wrong we will need to tweak things
        df = pd.read_csv(raw_pathway_file,sep='\s+')
        df = df.take([0,2],axis=1)
        df.to_csv(standardized_pathway_file, header=False,index=False,sep=' ')

