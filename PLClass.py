from src.PRM import PRM
import docker
import os

# These classes should probably each be in their own file.
# For initial debugging purposes, they are all listed here.


class PathLinker(PRM):

    def generate_inputs(self):
        print('PathLinker: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PathLinker: {} run() with {}'.format(self.name,self.params))

    # Temporary name for the static version of the runner
    # Skips parameter validation step
    @staticmethod
    def run_static(network=None, nodes=None, output=None, k=None):
        """
        Run PathLinker with Docker
        @param network: input network file
        @param nodes: input node types
        @param output: output directory
        @param k: path length (optional)
        """
        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not network or not nodes or not output:
            raise ValueError('Required PathLinker arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        command = ['python', '../run.py']
        if k:
            command.extend(['-k', str(k)])
        command.extend([network, nodes])
        print('PathLinker: run_static() command {}'.format(' '.join(command)))

        working_dir = os.getcwd()

        data_dir = os.path.join(working_dir, 'docker', 'pathlinker')
        # Tony can run this example successfully on Git for Windows even with the following lines commented out
        if os.name == 'nt':
            print("running on Windows")
            data_dir = str(data_dir).replace("\\", "/").replace("C:", "//c")

        try:
            container_output = client.containers.run('ajshedivy/pr-pathlinker:example',
                                command,
                                stderr=True,
                                volumes={data_dir: {'bind': '/home/PathLinker/data', 'mode': 'rw'}},
                                working_dir='/home/PathLinker'
                                )
            print(container_output.decode('utf-8'))

        finally:
            # Not sure whether this is needed
            client.close()

        # Need to rename the output file to match the specific output file in the params
        # Temporarily create a placeholder output file
        with open(output, 'w') as out_file:
            out_file.write('PathLinker: run_static() command {}'.format(' '.join(command)))

    def parse_output(self):
        print('PathLinker: {} parseOutput() from {}'.format(self.name,self.outputdir))


class BowTieBuilder(PRM):

    def generate_inputs(self):
        print('BowTieBuilder: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('BowTieBuilder: {} run() with {}'.format(self.name,self.params))

    def parse_output(self):
        print('BowTieBuilder: {} parseOutput() from {}'.format(self.name,self.outputdir))

class PCSF(PRM):

    def generate_inputs(self):
        print('PCSF: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PCSF: {} run() with {}'.format(self.name,self.params))

    def parse_output(self):
        print('PCSF: {} parseOutput() from {}'.format(self.name,self.outputdir))


if __name__ == '__main__':
    params = {
        'network': "network.txt",
        'nodes': "nodes.txt",
        'output': "outdir",
        'k': 10
    }

    PathLinker.run_static(**params)
