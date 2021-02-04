from docker.utils.utils import convert_volume_binds
from PRM import *
import docker 
import os
import sys

### These classes should probably each be in their own file.
### For initial debugging purposes, they are all listed here.
class PathLinker(PRM):

    def generateInputs(self):
        print('PathLinker: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        '''
        Run SINGE with the provided arguments
        '''

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        print(type(client.containers))
        command = ['python']
        command.append('../run.py')
        command.append('sample-in-net.txt')
        command.append('sample-in-nodetypes.txt')

        working_dir = os.getcwd()

        data = os.path.join(working_dir, 'docker', 'pathlinker')
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

    def parseOutput(self):
        print('PathLinker: {} parseOutput() from {}'.format(self.name,self.outputdir))


class BowTieBuilder(PRM):

    def generateInputs(self):
        print('BowTieBuilder: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('BowTieBuilder: {} run() with {}'.format(self.name,self.params))

    def parseOutput(self):
        print('BowTieBuilder: {} parseOutput() from {}'.format(self.name,self.outputdir))

class PCSF(PRM):

    def generateInputs(self):
        print('PCSF: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PCSF: {} run() with {}'.format(self.name,self.params))

    def parseOutput(self):
        print('PCSF: {} parseOutput() from {}'.format(self.name,self.outputdir))


if __name__ == '__main__':
    params = {
        'name': "",
        'inputdir': "",
        'outputdir': "",
        'params': {'k': 10}
    }

    pathlinker = PathLinker(params)
    pathlinker.run()

