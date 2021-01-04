from PRM import *


class PathLinker(PRM):

    def GenerateInputs(self):
        print('this method would take as input:\n{}\n{}'.format(self.params,self.inputdir))

    def Run(self):
        print('this method would run PL')

    def parseOutput(self):
        print('here we would access {}'.format(self.outputdir))

