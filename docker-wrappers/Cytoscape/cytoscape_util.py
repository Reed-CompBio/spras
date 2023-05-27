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
        "--pathway",
        dest='pathways',
        type=str,
        action='append',
        required=True,
        help='The path to a pathway file. Add the argument multiple times to visualize multiple pathways. '
             'Optionally use a | to append a label for the pathway such as path/to/file.txt|pathway_label'
    )

    parser.add_argument(
        "--outdir",
        dest='outdir',
        type=str,
        default='output',
        help='The output directory of the session file. Default: output'
    )

    parser.add_argument(
        "--outlabel",
        dest='outlabel',
        type=str,
        default='cytoscape-session',
        help='The output filename of the session file, which will have the extension .cys. Default: cytoscape-session'
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


def load_pathways(pathways: List[str], out_dir: str, out_label: str) -> None:
    if len(pathways) == 0:
        raise ValueError('One or more pathway files are required')

    start_remote_cytoscape()
    for pathway in pathways:
        path, name = parse_name(pathway)
        suid = p4c.networks.import_network_from_tabular_file(
            file=path,
            column_type_list="s,t,x",
            delimiters="\t"
        )
        p4c.networks.rename_network(name, network=suid)

    p4c.session.save_session(os.path.join(out_dir, out_label))


def main():
    opts = parse_arguments()
    load_pathways(opts.pathways, opts.outdir, opts.outlabel)


if __name__ == '__main__':
    main()
