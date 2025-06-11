import pandas as pd
from pathlib import Path

from spras.containers import prepare_volume, run_container
from spras.interactome import reinsert_direction_col_undirected
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['ST_RWR']

class ST_RWR(PRM):
    required_inputs = ['network','sources','targets']

    @staticmethod
    def generate_inputs(data, filename_map):
        for input_type in ST_RWR.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # Get seperate source and target nodes for source and target files
        if data.contains_node_columns(["sources","targets"]):
            sources = data.request_node_columns(["sources"])
            sources.to_csv(filename_map['sources'],sep='\t',index=False,columns=['NODEID'],header=False)

            targets = data.request_node_columns(["targets"])
            targets.to_csv(filename_map['targets'],sep='\t',index=False,columns=['NODEID'],header=False)
        else:
            raise ValueError("Invalid node data")

        # Get edge data for network file
        edges = data.get_interactome()
        edges.to_csv(filename_map['network'],sep='|',index=False,columns=['Interactor1','Interactor2'],header=False)

    @staticmethod
    def run(network=None, sources=None, targets=None, alpha=None, output_file=None,  container_framework="docker"):
        if not sources or not targets or not network or not output_file:
            raise ValueError('Required local_neighborhood arguments are missing')

        with Path(network).open() as network_f:
            for line in network_f:
                line = line.strip()
                endpoints = line.split("|")
                if len(endpoints) != 2:
                    raise ValueError(f"Edge {line} does not contain 2 nodes separated by '|'")

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, source_file = prepare_volume(sources, work_dir)
        volumes.append(bind_path)

        bind_path, target_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        # ST_RWR does not provide an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # ST_RWR requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + "/output.txt"
        command = ['python',
                   '/ST_RWR/ST_RWR.py',
                   '--network',network_file,
                   '--sources',source_file,
                   '--targets',target_file,
                   '--output', mapped_out_prefix]

        # Add alpha as an optional argument
        if alpha is not None:
            command.extend(['--alpha', str(alpha)])

        container_suffix = 'st-rwr:latest'
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)

        print(out)
        # Rename the primary output file to match the desired output filename
        output_edges = Path(out_dir, 'output.txt')
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=0)
        if not df.empty:
            df.columns = ['node','score']
            if params is not None:
                threshold = params.get('threshold')
                df = df[df.score >= threshold]
            raw_dataset = pd.read_pickle(params.get('dataset'))
            interactome = raw_dataset.get_interactome().get(['Interactor1','Interactor2'])
            interactome = interactome[interactome['Interactor1'].isin(df['node'])
                                      & interactome['Interactor2'].isin(df['node'])]
            interactome = add_rank_column(interactome)
            interactome = reinsert_direction_col_undirected(interactome)
            interactome.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            interactome, has_duplicates = duplicate_edges(interactome)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
            interactome.to_csv(standardized_pathway_file, header = True, index=False, sep='\t')
