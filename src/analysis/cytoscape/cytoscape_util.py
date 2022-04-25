import argparse
from pathlib import PurePath
import pathlib
from py2cytoscape import cyrest
import time
import sys
import os
from py2cytoscape.data.cyrest_client import CyRestClient
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError
from json.decoder import JSONDecodeError
import sys

SPRAS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def load_outputs() -> None:
    """visualize tps outputs in cytoscape via py2cytoscape API
    Args:
        cyclient (CyRestClient) : RESTful client for cytoscape
        network_file (str)      : tps network file
        annot_file (str)        : tps generated node annotations
        style_file (str)        : tps style file
        data_types (str)        : tps annotation column data types
        save_file (str)         : cytoscape session file name
    """
    cy = CyRestClient()
    cyclient = cyrest.cyclient()
    files = get_pathway_files()
    cy.session.delete()
    for file in files:
        path_to_file = os.path.join(SPRAS_ROOT, file)
        print(path_to_file)
        cy.network.create(collection=file)
        suid = cyclient.network.import_file(
            defaultInteraction="interacts with",
            afile=path_to_file,
            delimiters=" ",
            firstRowAsColumnNames=False,
            startLoadRow='0',
            indexColumnSourceInteraction='1',
            indexColumnTargetInteraction='2',
            dataTypeList='s,s,i'
        )
        print(suid)
        time.sleep(1)

def load_pathways():
    connection_count = 0
    json_count = 0
    http_count = 0
    switch = False
    start = time.time()
    while not switch:
        try:
            print('loading tps and annotation outputs ... ')
            load_outputs()
            switch = True
        except ConnectionError as e:
            connection_count += 1
            time.sleep(2)
            continue
        except JSONDecodeError as e:
            json_count += 1
            time.sleep(2)
            continue
        except HTTPError as e:
            http_count += 1
            time.sleep(2)
            continue
    end = time.time()

    print(f'time elapsed: {end-start}')


def get_pathway_files():
    
    files = os.path.join(SPRAS_ROOT, 'output', 'pathways.txt')
    networks = []
    with open(files, 'r') as f:
        networks = f.read().splitlines()
    
    return networks


def main():
    load_pathways()
