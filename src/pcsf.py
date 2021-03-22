from src.PRM import *

class PCSF(PRM):

    def generate_inputs(self):
        print('PCSF: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PCSF: {} run() with {}'.format(self.name,self.params))

    def parse_output(self):
        print('PCSF: {} parseOutput() from {}'.format(self.name,self.outputdir))
