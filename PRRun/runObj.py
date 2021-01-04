import abc 

class RunnerObject(abc.ABC):
    @abc.abstractmethod
    def generateInputs(self):
        pass

    @abc.abstractmethod
    def run(self):
        pass

    @abc.abstractmethod
    def parseOutput(self):
        pass

class Helper:
    pass
