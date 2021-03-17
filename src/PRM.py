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
        # debugging
        #print('Params:',self.params)


    @abstractmethod
    def generate_inputs(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def parse_output(self):
        pass
