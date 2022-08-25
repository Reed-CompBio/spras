import argparse
import os
import subprocess
import time
from typing import List

import py4cytoscape as p4c
from requests.exceptions import RequestException

SLEEP_INTERVAL = 10


def get_parser() -> argparse.ArgumentParser:
    """
    :return: an argparse ArgumentParser object for parsing command
        line parameters
    """
    parser = argparse.ArgumentParser(
        description='Visualize pathway files from SPRAS.')

    parser.add_argument(
        "--files",
        dest='files',
        type=str,
        action='append',
        required=True
    )

    parser.add_argument(
        "--outdir",
        dest='outdir',
        type=str,
        default='output'
    )

    return parser


def parse_arguments() -> argparse.Namespace:
    """
    Initialize a parser and use it to parse the command line arguments
    :return: parsed dictionary of command line arguments
    """
    parser = get_parser()
    opts = parser.parse_args()

    return opts


def start_remote_cytoscape() -> None:
    try:
        subprocess.run([
            "/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"
        ],
            check=True)
    except subprocess.CalledProcessError as e:
        print('An error has occurred while trying to run Cytoscape\n' + str(e), flush=True)

    connected = False
    # Allow initial time to start up before trying to connect
    time.sleep(SLEEP_INTERVAL)
    while not connected:
        try:
            p4c.cytoscape_ping()
            print("Connected to Cytoscape", flush=True)
            connected = True
        except (RequestException, p4c.exceptions.CyError):
            print("Pinging Cytoscape, waiting for connection... ", flush=True)
            time.sleep(SLEEP_INTERVAL)
            pass
        except Exception as e:
            print(e)
            print("Pinging Cytoscape, waiting for connection... ", flush=True)
            time.sleep(SLEEP_INTERVAL)


def load_pathways(files: List[str], out_dir: str) -> None:
    if len(files) == 0:
        raise ValueError('One or more pathway files are required')

    start_remote_cytoscape()
    for file in files:
        suid = p4c.networks.import_network_from_tabular_file(
            file=file,
            column_type_list="s,t,x",
            delimiters=" "
        )
        p4c.networks.rename_network(file, network=suid)

    p4c.session.save_session(os.path.join(out_dir, 'cytoscape-session'))


def main():
    opts = parse_arguments()
    load_pathways(opts.files, opts.outdir)


if __name__ == '__main__':
    main()
