from src.PRM import *

class BowTieBuilder(PRM):

    def generate_inputs(self):
        print('BowTieBuilder: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('BowTieBuilder: {} run() with {}'.format(self.name,self.params))

    def parse_output(self):
        print('BowTieBuilder: {} parseOutput() from {}'.format(self.name,self.outputdir))
