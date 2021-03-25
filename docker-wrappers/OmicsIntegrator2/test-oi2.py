import docker
import os


def main():
    """
    Run Omics Integrator 2 in the Docker image using hard-coded arguments.
    """
    # Initialize a Docker client using environment variables
    client = docker.from_env()

    edge_file = 'oi2-edges.txt'
    prize_file = 'oi2-prizes.txt'
    out_dir = '.'

    command = ['OmicsIntegrator', '-e', edge_file, '-p', prize_file, '-o', out_dir]

    print('Running Omics Integrator 2 with arguments: {}'.format(' '.join(command)), flush=True)

    working_dir = os.getcwd()
    input_dir = os.path.join(working_dir, '..', '..', 'input')

    try:
        out = client.containers.run('agitter/omics-integrator-2',
                              command,
                              stderr=True,
                              volumes={input_dir: {'bind': '/OmicsIntegrator2', 'mode': 'rw'}},
                              working_dir='/OmicsIntegrator2')
        print(out.decode('utf-8'))
    finally:
        # Not sure whether this is needed
        client.close()


if __name__ == '__main__':
    main()
