import yaml
import argparse
import itertools
from collections import defaultdict
from pathlib import Path
import multiprocessing
from multiprocessing import Pool, cpu_count
import concurrent.futures
import yaml
import argparse
import itertools
from collections import defaultdict
from pathlib import Path
import multiprocessing
from multiprocessing import Pool, cpu_count
import concurrent.futures
from typing import Dict, List
from PRRun.runner import Runner
import os

import PRRun as br
yaml.warnings({'YAMLLoadWarning': False})


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


    with open(config_file, 'r') as conf:
        evaluation = br.ConfigParser.parse(conf)
    print(evaluation)
    print('Evaluation started')
    # print("--- runners")
    # print(evaluation.input_settings.algorithms)
    # print(evaluation.input_settings.datasets)
    


    for idx in range(len(evaluation.runners)):
        evaluation.runners[idx].generateInputs()

    for idx in range(len(evaluation.runners)):
        evaluation.runners[idx].run()

    for idx in range(len(evaluation.runners)):
        evaluation.runners[idx].parseOutput()

    print('Evaluation complete')


if __name__ == '__main__':
  main()
