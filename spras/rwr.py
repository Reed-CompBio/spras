from spras.prm import PRM
from spras.containers import prepare_volume, run_container
from pathlib import Path
from spras.interactome import reinsert_direction_col_undirected
from spras.util import duplicate_edges, raw_pathway_df, add_rank_column
import pandas as pd

__all__ = ['RWR']

class RWR(PRM):
    required_inputs = ['network','nodes']

    @staticmethod
    def generate_inputs(data, filename_map):

        for input_type in RWR.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns(["sources","targets"]):
            sources = data.request_node_columns(["sources"])
            targets = data.request_node_columns(["targets"])
            nodes = pd.DataFrame({'NODEID':sources['NODEID'].tolist() + targets['NODEID'].tolist()})
            nodes.to_csv(filename_map['nodes'],sep='\t',index=False,columns=['NODEID'],header=False)
        else:
            raise ValueError("Invalid node data")

        edges = data.get_interactome()

        edges.to_csv(filename_map['network'],sep='|',index=False,columns=['Interactor1','Interactor2'],header=False)
        

    @staticmethod
    def run(network=None, nodes=None, alpha=None, output_file=None,  container_framework="docker"):
       
        if not nodes:
            raise ValueError('Required RWR arguments are missing')

        with Path(network).open() as network_f:
            for line in network_f:
                line = line.strip()
                endpoints = line.split("|")
                if len(endpoints) != 2:
                    raise ValueError(f"Edge {line} does not contain 2 nodes separated by '|'") 
        work_dir = '/spras'

        volumes = list()

        bind_path, nodes_file = prepare_volume(nodes, work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)  

        out_dir = Path(output_file).parent     
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + "/out"
        command = ['python',
                   '/RWR/RWR.py',
                   '--network',network_file,
                   '--nodes',nodes_file,
                   '--output', mapped_out_prefix]
        
        if alpha is not None:
            command.extend(['--alpha', str(alpha)])

        container_suffix = 'rwr'
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        
        print(out)
        output_edges = Path(out_dir,'out')
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
     
        df = raw_pathway_df(raw_pathway_file, sep='\t')
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_undirected(df)
            df.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
        df.to_csv(standardized_pathway_file, header = True, index=False, sep='\t')
