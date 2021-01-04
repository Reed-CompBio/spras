from PRM import *

### These classes should probably each be in their own file.
### For initial debugging purposes, they are all listed here.
class PathLinker(PRM):

    def generateInputs(self):
        print('PathLinker: {} generateInputs() from {}'.format(self.name,self.inputdir))

    def run(self):
        print('PathLinker: {} run() with {}'.format(self.name,self.params))

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
