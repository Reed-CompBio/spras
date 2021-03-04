from src.PRM import *

class PCSF(PRM):

    def generateInputs(self):
        print('PCSF: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PCSF: {} run() with {}'.format(self.name,self.params))

    def parseOutput(self):
        print('PCSF: {} parseOutput() from {}'.format(self.name,self.outputdir))