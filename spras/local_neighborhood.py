from spras.prm import PRM
from pathlib import Path
from spras.containers import prepare_volume, run_container
import pandas as pd
from spras.interactome import(reinsert_direction_col_directed)
from spras.util import(add_rank_column)

__all__ = ["LocalNeighborhood"]

class LocalNeighborhood(PRM):
    required_inputs = ['network','nodes']

    def generate_inputs(data,filename_map):
        for input_type in LocalNeighborhood.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")
        # raises error if filenames are missing

        if data.contains_node_columns('prize'):
            node_df = data.request_node_columns(['prize'])
        elif data.contains_node_columns(['prize']):
            # if there are not prizes but there are sources/targets, then it assigns prizes based on those
            node_df = data.request_node_columns(['sources','targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            # raises error if there are no prizes, sources, or targets
            raise ValueError("Local Neighborhood requires node prizes or sources and targets")

        node_df.to_csv(filename_map['nodes'],index=False,columns=['NODEID'],header=False)

        edges_df = data.get_interactome()
        
        edges_df.to_csv(filename_map['network'],index=False,sep = "|",columns=['Interactor1','Interactor2'], header=False)
        
    def run(nodes=None, network=None, output_file=None, container_framework='docker'):
        if not nodes or not network or not output_file:
            raise ValueError('Required arguments are missing')
        work_dir = '/spras'

        volumes = list()

        bind_path, node_file = prepare_volume(nodes,work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent

        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir),work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/out'
        
        command = ['python','/LocalNeighborhood/local_neighborhood.py','--network',network_file,'--nodes',node_file,'--output', mapped_out_prefix]
        
        container_suffix = 'local-neighborhood'
        out = run_container(container_framework, container_suffix, command, volumes, work_dir)

        output_edges = Path(out_dir,'out')
        output_edges.rename(output_file)
    def parse_output(raw_pathway_file, standardized_pathway_file):
        df = pd.read_csv(raw_pathway_file, sep='|', header=None)
        df = add_rank_column(df)
        df = reinsert_direction_col_directed(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
