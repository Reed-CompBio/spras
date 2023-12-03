import argparse
import subprocess
import time
from typing import List

import py4cytoscape as p4c
from requests.exceptions import RequestException

SLEEP_INTERVAL = 10
MAX_CONNECTION_ATTEMPTS = 20


def get_parser() -> argparse.ArgumentParser:
    """
    :return: an argparse ArgumentParser object for parsing command
        line parameters
    """
    parser = argparse.ArgumentParser(
        description='Visualize pathway files from SPRAS.')

    parser.add_argument(
        "--pathway",
        dest='pathways',
        type=str,
        action='append',
        required=True,
        help='The path to a pathway file. Add the argument multiple times to visualize multiple pathways. '
             'Optionally use a | to append a label for the pathway such as path/to/file.txt|pathway_label'
    )

    parser.add_argument(
        "--output",
        dest='output',
        type=str,
        default='cytoscape-session.cys',
        help='The output filename of the Cytoscape session file, which will have the extension .cys added if it is not '
             'already provided. Default: cytoscape-session.cys'
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
    """
    Use supervisord to start the Cytoscape process. Ping Cytoscape until a connection is established and sleep in
    between pings. Raises an error if Cytoscape cannot be reached within the maximum number of attempts.
    """
    try:
        subprocess.run([
            '/usr/bin/supervisord', '-c', '/etc/supervisor/conf.d/supervisord.conf'
        ],
            check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('An error has occurred while trying to run Cytoscape') from e

    connected = False
    attempts = 0
    # Allow initial time to start up before trying to connect
    time.sleep(SLEEP_INTERVAL)
    while not connected and attempts < MAX_CONNECTION_ATTEMPTS:
        attempts += 1
        try:
            p4c.cytoscape_ping()
            print('Connected to Cytoscape', flush=True)
            connected = True
        except (RequestException, p4c.exceptions.CyError):
            print('Pinging Cytoscape, waiting for connection... ', flush=True)
            time.sleep(SLEEP_INTERVAL)
            pass
        except Exception as e:
            print(e)
            print('Pinging Cytoscape, waiting for connection... ', flush=True)
            time.sleep(SLEEP_INTERVAL)

    if not connected:
        raise ConnectionError('Could not connect to Cytoscape')


def parse_name(pathway: str) -> (str, str):
    """
    Extract the optional label from the pathway argument
    @param pathway: the command line pathway argument, which may contain a | separated label
    @return: a tuple with the file path and the label
    """
    parts = pathway.split('|')
    # No label provided or empty label provided so the file path is the label
    if len(parts) == 1 or len(parts[1]) == 0:
        return parts[0], parts[0]
    # A valid label was provided
    else:
        return parts[0], parts[1]


def load_pathways(pathways: List[str], output: str) -> None:
    """
    Launch and connect to Cytoscape, import all pathways, and save a session file
    @param pathways: the list of pathways to import
    @param output: the name of the Cytoscape session file to save
    """
    if len(pathways) == 0:
        raise ValueError('One or more pathway files are required')

    start_remote_cytoscape()
    for pathway in pathways:
        path, name = parse_name(pathway)
        suid = p4c.networks.import_network_from_tabular_file(
            file=path,
            column_type_list='s,t,x,ea',
            delimiters='\t'
        )
        p4c.networks.rename_network(name, network=suid)

    p4c.session.save_session(output)


def main():
    """
    Main function
    """
    opts = parse_arguments()
    load_pathways(opts.pathways, opts.output)


if __name__ == '__main__':
    main()
