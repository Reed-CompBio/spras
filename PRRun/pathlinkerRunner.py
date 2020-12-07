import os

def generateInputs(RunnerObj):
    '''
    Function to generate desired inputs for PathLinker.
    If the folder/files under RunnerObj.datadir exist, 
    this function will not do anything.
    '''

    print("generate inputs")
    if not RunnerObj.inputDir.joinpath("PATHLINKER").exists():
        print("Input folder for JUMP3 does not exist, creating input folder...")
        RunnerObj.inputDir.joinpath("PATHLINKER").mkdir(exist_ok = False)

    
    
def run(RunnerObj):
    '''
    Function to run pathlinker algorithm
    '''
    print('run')



def parseOutput(RunnerObj):
    '''
    Function to parse outputs from pathlinker.
    '''
    print("parse output")