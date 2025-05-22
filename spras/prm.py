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

    @property
    @abstractmethod
    def required_inputs(self):
        raise NotImplementedError

    @abstractmethod
    def generate_inputs(self):
        raise NotImplementedError

    @abstractmethod
    def run(self):
        raise NotImplementedError

    @abstractmethod
    def parse_output(self):
        raise NotImplementedError
