from src.PRM import *

class BowTieBuilder(PRM):

    def generateInputs(self):
        print('BowTieBuilder: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('BowTieBuilder: {} run() with {}'.format(self.name,self.params))

    def parseOutput(self):
        print('BowTieBuilder: {} parseOutput() from {}'.format(self.name,self.outputdir))