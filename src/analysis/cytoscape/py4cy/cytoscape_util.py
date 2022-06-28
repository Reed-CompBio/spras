import argparse
from pathlib import Path, PurePath
import pathlib
from typing import List, Dict, Any
from numpy import append
import py4cytoscape as p4c
import time
import sys
import os
from requests.exceptions import RequestException
import subprocess

SPRAS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def get_parser() -> argparse.ArgumentParser:
    '''
    :return: an argparse ArgumentParser object for parsing command
        line parameters
    '''
    parser = argparse.ArgumentParser(
        description='Run SPRAS Cytoscape pipeline.')

    parser.add_argument(
        "--files",
        action='append'
    )

    parser.add_argument(
        "--outdir", 
        default='output'
    )

    return parser

def parse_arguments() -> Dict[str, Any]:
    '''
    Initialize a parser and use it to parse the command line arguments
    :return: parsed dictionary of command line arguments
    '''
    parser = get_parser()
    opts = parser.parse_args()

    return opts

def get_pathway_files():
    
    files = os.path.join(SPRAS_ROOT, 'output', 'pathways.txt')
    networks = []
    with open(files, 'r') as f:
        networks = f.read().splitlines()
    
    return networks

def start_remote_cytoscape() -> None:
    print('start supervisord client', flush=True)
    try:
        subprocess.run([
            "/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"
        ],
        check=True)
    except subprocess.CalledProcessError as e:
        print('an error has occurred while trying to run TPS\n\n' + str(e))

    connected = False
    while not connected:
        try:
            p4c.cytoscape_ping()
            print("connected!", flush=True)
            connected = True
        except (RequestException,  p4c.exceptions.CyError) as e:
            print("pinging Cytoscape, waiting for connection ... ", flush=True)
            time.sleep(4)
            pass
        except Exception as e:
            print(e)
            print("pinging Cytoscape, waiting for connection ... ", flush=True)
            time.sleep(4)


def load_pathways(files: List[str], out_dir: str) -> None:
    start_remote_cytoscape()
    for file in files:
        suid = p4c.networks.import_network_from_tabular_file(
            file=file,
            column_type_list="s,t,x",
            delimiters=" "
        )
        print(suid, flush=True)
        p4c.networks.rename_network(file, network=suid)

    p4c.session.save_session(out_dir+'/cytoscape-session')

def main():
    opts = parse_arguments()
    load_pathways(opts.files, opts.outdir)

if __name__ == '__main__':
    main()
