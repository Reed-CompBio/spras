import PRRun.pathlinkerRunner as PATHLINKER

from pathlib import Path


# InputMapper = {'PATHLINKER':PATHLINKER.generateInputs}

# AlgorithmMapper = {'PATHLINKER': PATHLINKER.run}

# OutputParser = {'PATHLINKER': PATHLINKER.parseOutput}



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
        print(self.name)
        InputMapper[self.name](self)
        
        
    def run(self):
        print("Runner: run ")
        AlgorithmMapper[self.name](self)


    def parseOutput(self):
        print("Runner: parse outputs")
        OutputParser[self.name](self)