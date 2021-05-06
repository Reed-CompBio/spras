import docker
import os

DEFAULT_OUT_DIR = 'output'

def run(expression=None, genes=None, out_dir=DEFAULT_OUT_DIR, hyperparameters=None):
    '''
    Run SINGE with the provided arguments
    '''
    if not expression or not genes or not hyperparameters:
        raise ValueError('Required SINGE arguments are missing')

    # Initialize a Docker client using environment variables
    client = docker.from_env()

    # First argument will always be 'standalone'
    command = ['standalone']
    command.append(expression)
    command.append(genes)
    command.append(out_dir)
    command.append(hyperparameters)
    print('Running SINGE with arguments: {}'.format(' '.join(command)), flush=True)

    working_directory = os.getcwd()

    try:
        out = client.containers.run('agitter/singe:0.4.1',
                              command,
                              stderr=True,
                              volumes={working_directory: {'bind': '/SINGE', 'mode': 'rw'}},
                              working_dir='/SINGE')
        print(out.decode('utf-8'))
    finally:
        # Not sure whether this is needed
        client.close()

        # Clean up temporary file SINGE leaves
        if os.path.exists('TempMat.mat'):
            os.remove('TempMat.mat')

def main():
    '''
    Run SINGE in the Docker image using hard-coded arguments.
    '''
    #args = {'expression': 'input/X_SCODE_data.mat',
    #        'genes': 'input/gene_list.mat',
    #        'out_dir': 'output',
    #        'hyperparameters': 'input/example_hyperparameters.txt'}
    # Example using a default argument (out_dir)
    args = {'expression': 'input/X_SCODE_data.mat',
            'genes': 'input/gene_list.mat',
            'hyperparameters': 'input/example_hyperparameters.txt'}

    run(**args)

if __name__ == '__main__':
    main()
