import yaml
import argparse

# supported algorithm imports
from src.pathlinker import PathLinker as pathlinker

import PRRun as br
yaml.warnings({'YAMLLoadWarning': False})

def run(algorithm, params):
    """
    A generic interface to the algorithm-specific run functions
    """
    try:
        globals()[algorithm.lower()].run_static(**params)
    except:
        raise NotImplementedError('Only PathLinker is currently supported :(')

def get_parser() -> argparse.ArgumentParser:
    '''
    :return: an argparse ArgumentParser object for parsing command
        line parameters
    '''
    parser = argparse.ArgumentParser(
        description='Run pathway reconstruction pipeline.')

    parser.add_argument('--config', default='config.yaml',
        help='Path to config file')

    return parser

def parse_arguments():
    '''
    Initialize a parser and use it to parse the command line arguments
    :return: parsed dictionary of command line arguments
    '''
    parser = get_parser()
    opts = parser.parse_args()

    return opts

def main():
    opts = parse_arguments()
    config_file = opts.config
    print("########################## Run PRRunner ##########################")
    print("print output follows execution of PRRunner \n'*' denotes calls from PRRunner\n")
    print("* create Evaluation")
    with open(config_file, 'r') as conf:
        evaluation = br.ConfigParser.parse(conf)
    print(evaluation)
    print("-------------------------------------------")
    print('* Evaluation started')
    # print("--- runners")
    # print(evaluation.input_settings.algorithms)
    # print(evaluation.input_settings.datasets)
    

    print("* --generate Inputs driver loop")
    for idx in range(len(evaluation.runners)):
        
        evaluation.runners[idx].generateInputs()
        print("\n")

    print("* --run driver loop")
    for idx in range(len(evaluation.runners)):
        
        evaluation.runners[idx].run()
        print("\n")

    print("* --parse outputs driver loop")
    for idx in range(len(evaluation.runners)):
        
        evaluation.runners[idx].parseOutput()
        print("\n")

    print('* Evaluation complete')


if __name__ == '__main__':
  main()
