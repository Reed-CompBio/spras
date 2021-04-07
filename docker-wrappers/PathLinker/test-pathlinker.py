import docker
import os
import sys


def main():
    """
    Run PathLinker in the Docker image using hard-coded arguments.
    """
    # Initialize a Docker client using environment variables
    client = docker.from_env()

    net_file = 'sample-in-net.txt'
    nodetypes_file = 'sample-in-nodetypes.txt'

    command = [
        'python', '../run.py', net_file, nodetypes_file
    ]

    print('Running PathLinker with arguments: {}'.format(' '.join(command)), flush=True)

    working_dir = os.getcwd()
    data = os.path.join(working_dir, 'data')
    if os.name == 'nt':
        print("running on Windows")
        data = str(data).replace("\\", "/").replace("C:", "//c")

    try:
        out = client.containers.run(
            'ajshedivy/pathlinker',
            command,
            stderr=True,
            volumes={data: {'bind': '/home/PathLinker/data', 'mode': 'rw'}},
            working_dir='/home/PathLinker/data'
        )
        print(out.decode('utf-8'))
    finally:
        # Not sure whether this is needed
        client.close()


if __name__ == '__main__':
    main()