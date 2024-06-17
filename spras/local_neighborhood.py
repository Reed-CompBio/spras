from spras.prm import PRM
from pathlib import Path
from spras.containers import prepare_volume, run_container
import pandas as pd

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

        node_df.to_csv(filename_map['prizes'],sep='\t',indez=False,columns=['NODEID','prize'],header=['name','prize'])

        edges_df = data.get_interactome()
        
        edges_df.to_csv(filename_map['edges'],sep='\t',index=False,
                        columns=['Interactor1','Interactor2','Weight','Direction']
                        header=['protein1','protein2','weight','directionality'])
    def run(nodetypes=None, network=None, output_file=None, k=None, container_framework='docker'):
        if not nodetypes or not network or not output_file:
            raise ValueError('Required Pathlinker arguments are missing')
        work_dir = '/spras'

        volumes = list()

        bind_path, node_file = prepare_volume(nodetypes,work_dir)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        mapped_out_dir = prepare_volume(str(out_dir),work_dir)
        mapped_out_prefix = mapped_out_dir + '/out'
        command = ['python','/LocalNeighborhood/run.py',network_file,node_file,'--output', mapped_out_prefix]
        container_suffix = 'local-neighborhood'
        out = run_container(container_framework, container_suffix, command, volumes, work_dir)
    def parse_output(raw_pathway_file, standardized_pathway_file):
        df = pd.read_csv(raw_pathway_file, sep='\t').take([0, 1, 2], axis=1)
        df = reinsert_direction_col_directed(df)
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
