import docker
import os

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


def main():
    """
    Run Omics Integrator 1 in the Docker image using hard-coded arguments.
    """
    # Initialize a Docker client using environment variables
    client = docker.from_env()

    working_dir = os.getcwd()
    input_dir = os.path.join(working_dir, '..', '..', 'input')

    edge_file = 'oi1-edges.txt'
    prize_file = 'oi2-prizes.txt' # Prize file format is the same for versions 1 and 2
    out_dir = '.'

    conf_filename = 'oi1-configuration.txt'
    conf_file = os.path.join(input_dir, conf_filename)
    write_conf(conf_file)

    command = ['python', '/OmicsIntegrator/scripts/forest.py', '--edge', edge_file, '--prize', prize_file, '--conf', conf_filename,
               '--msgpath', '/OmicsIntegrator/msgsteiner-1.3/msgsteiner',
               '--outpath', out_dir, '--outlabel', 'oi1']

    print('Running Omics Integrator 1 with arguments: {}'.format(' '.join(command)), flush=True)

    try:
        out = client.containers.run('agitter/omics-integrator-1',
                              command,
                              stderr=True,
                              volumes={input_dir: {'bind': '/OmicsIntegrator1', 'mode': 'rw'}},
                              working_dir='/OmicsIntegrator1')
        print(out.decode('utf-8'))
    finally:
        # Not sure whether this is needed
        client.close()
        if os.path.isfile(conf_file):
            os.remove(conf_file)


if __name__ == '__main__':
    main()
