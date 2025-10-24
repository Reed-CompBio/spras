from pathlib import Path

import pandas as pd

from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['RWR']

class RWR(PRM):
    required_inputs = ['network','nodes']
    dois = []

    @staticmethod
    def generate_inputs(data, filename_map):
        RWR.validate_required_inputs(filename_map)

        # Get sources and targets for node input file
        if data.contains_node_columns(["sources","targets"]):
            sources = data.get_node_columns(["sources"])
            targets = data.get_node_columns(["targets"])
            nodes = pd.DataFrame({'NODEID':sources['NODEID'].tolist() + targets['NODEID'].tolist()})
            nodes.to_csv(filename_map['nodes'],sep='\t',index=False,columns=['NODEID'],header=False)
        else:
            raise ValueError("Invalid node data")

        # Get edge data for network file
        edges = data.get_interactome()
        edges = convert_undirected_to_directed(edges)

        edges.to_csv(filename_map['network'],sep='|',index=False,columns=['Interactor1','Interactor2'],header=False)

    @staticmethod
    def run(network=None, nodes=None, alpha=None, output_file=None, container_settings=None, threshold=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        if not nodes:
            raise ValueError('Required RWR arguments are missing')

        with Path(network).open() as network_f:
            for line in network_f:
                line = line.strip()
                endpoints = line.split("|")
                if len(endpoints) != 2:
                    raise ValueError(f"Edge {line} does not contain 2 nodes separated by '|'")
        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, nodes_file = prepare_volume(nodes, work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir, container_settings)
        volumes.append(bind_path)

        # RWR does not provide an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # RWR requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir, container_settings)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + "/output.txt"
        command = ['python',
                   '/RWR/RWR.py',
                   '--network', network_file,
                   '--nodes', nodes_file,
                   '--output', mapped_out_prefix]

        # Add alpha as an optional argument
        if alpha is not None:
            command.extend(['--alpha', str(alpha)])

        container_suffix = 'rwr:v1'
        run_container_and_log(
            "RandomWalk with Restart",
            container_suffix,
            command,
            volumes,
            work_dir,
            out_dir,
            container_settings)

        # Rename the primary output file to match the desired output filename
        output_edges = Path(out_dir, 'output.txt')
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        df = raw_pathway_df(raw_pathway_file, sep='\t',header=0)
        if not df.empty:
            df.columns = ['node', 'score']
            if 'threshold' not in params:
                raise ValueError("threshold is a required parameter.")
            threshold = params['threshold']
            df = df.drop_duplicates(subset=['node'])
            df = df.sort_values(by=['score'], ascending=False)
            df = df.head(int(threshold))
            raw_dataset = Dataset.from_file(params.get('dataset'))
            interactome = raw_dataset.get_interactome().get(['Interactor1','Interactor2'])
            interactome = interactome[interactome['Interactor1'].isin(df['node'])
                                      & interactome['Interactor2'].isin(df['node'])]
            interactome = add_rank_column(interactome)
            interactome = reinsert_direction_col_directed(interactome)
            interactome.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            interactome, has_duplicates = duplicate_edges(interactome)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
            df = interactome
        df.to_csv(standardized_pathway_file, header = True, index=False, sep='\t')
