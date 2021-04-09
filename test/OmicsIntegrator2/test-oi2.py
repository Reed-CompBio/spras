import docker
from pathlib import Path


def main():
    """
    Run Omics Integrator 2 in the Docker image using hard-coded arguments.
    """
    # Initialize a Docker client using environment variables
    client = docker.from_env()
    working_dir = Path(__file__).parent.absolute()

    edge_file = Path('input', 'oi2-edges.txt')
    prize_file = Path('input', 'oi2-prizes.txt')

    out_dir = Path('output')
    # Omics Integrator 2 requires that the output directory exist
    Path(working_dir, out_dir).mkdir(parents=True, exist_ok=True)

    command = ['OmicsIntegrator', '-e', edge_file.as_posix(), '-p', prize_file.as_posix(),
               '-o', out_dir.as_posix(), '-g', '0']

    print('Running Omics Integrator 2 with arguments: {}'.format(' '.join(command)), flush=True)

    try:
        out = client.containers.run('agitter/omics-integrator-2',
                              command,
                              stderr=True,
                              volumes={working_dir.as_posix(): {'bind': '/OmicsIntegrator2', 'mode': 'rw'}},
                              working_dir='/OmicsIntegrator2')
        print(out.decode('utf-8'))
    finally:
        # Not sure whether this is needed
        client.close()


if __name__ == '__main__':
    main()
