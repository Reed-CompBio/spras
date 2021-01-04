import PRRun.pathlinkerRunner as PATHLINKER

from pathlib import Path


class Runner(object):
    '''
    A runnable analysis to be incorporated into the pipeline
    '''
    def __init__(self,
                params):
        '''
        params: dict created in PRRun

        '''
        print("init Runner object")
        self.name = params['name']
        self.inputDir = params['inputDir']
        self.params = params['params']
        self.exprData = params['exprData']
        self.cellData = params['cellData']
        
    def generateInputs(self):
        print("Runner: generate Inputs")
        module = globals()[self.name]
        getattr(module, 'generateInputs')(self)
        
        
    def run(self):
        print("Runner: run ")
        module = globals()[self.name]
        getattr(module, 'run')(self)


    def parseOutput(self):
        print("Runner: parse outputs")
        module = globals()[self.name]
        getattr(module, 'parseOutput')(self)