#
# Implement an abstract PRM class
#
# 
from abc import ABC, abstractmethod

class PRM(ABC):
    def __init__(self, params):
        self.name = params['name']
        self.inputdir = params['inputdir']
        self.outputdir = params['outputdir']
        self.params = params['params']


    @abstractmethod
    def GenerateInputs(self):
        pass

    @abstractmethod
    def Run(self):
        pass

    @abstractmethod
    def parseOutput(Self):
        pass

