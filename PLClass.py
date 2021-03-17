from src.PRM import PRM
import docker
import os

### These classes should probably each be in their own file.
### For initial debugging purposes, they are all listed here.


class PathLinker(PRM):

    def generate_inputs(self):
        print('PathLinker: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PathLinker: {} run() with {}'.format(self.name,self.params))

    # Temporary name for the static version of the runner
    # Skips parameter validation step
    @staticmethod
    def run_static(params):
        """
        params: a dictionary with the input file, output file, and k value
        """
        print('PathLinker: run_static() with {}'.format(params))

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        print(type(client.containers))
        command = ['python']
        command.append('../run.py')
        # Use the actual input files from the params here
        # Need to implement the generate_inputs function first
        command.append('sample-in-net.txt')
        command.append('sample-in-nodetypes.txt')
        # command.extend(['-k', params['k']])
        print(command)

        working_dir = os.getcwd()

        data = os.path.join(working_dir, 'docker', 'pathlinker')
        # Tony can run this example successfully on Git for Windows even with the following lines commented out
        if os.name == 'nt':
            print("running on Windows")
            data = str(data).replace("\\", "/").replace("C:", "//c")

        print(data)
        
        try:
            out = client.containers.run('ajshedivy/pr-pathlinker:example',
                                command, 
                                stderr=True,
                                volumes={data: {'bind': '/home/PathLinker/data', 'mode': 'rw'}},
                                working_dir='/home/PathLinker'
                                )
            print(out.decode('utf-8'))


        finally:
            # Not sure whether this is needed
            client.close()

        # Need to rename the output file to match the specific output file in the params?
        # Temporarily create a placeholder output file
        with open(params['output'], 'w') as out_file:
            out_file.write('PathLinker: run_static() with {}'.format(params))

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
        'name': "",
        'inputdir': "",
        'outputdir': "",
        'params': {'k': 10}
    }

    pathlinker = PathLinker(params)
    pathlinker.run_static(params)

