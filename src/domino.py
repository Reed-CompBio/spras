from src.prm import PRM
from pathlib import Path
from src.util import prepare_volume, run_container

import subprocess
import json
import pandas as pd

__all__ = ['DOMINO']

class DOMINO(PRM):
    required_inputs = ['network', 'active_genes']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in DOMINO.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        #Get active genes for node input file
        if data.contains_node_columns('active'):
            #NODEID is always included in the node table
            node_df = data.request_node_columns(['active'])
        else:
            raise ValueError("DOMINO requires active genes")

        #Create active_genes file
        node_df.to_csv(filename_map['active_genes'],sep="\t",index=False,columns=['NODEID'], header=False)

        #Create network file
        edges_df = data.get_interactome()
        edges_df['ppi'] = 'ppi'
        edges_df.to_csv(filename_map['network'],sep='\t',index=False,columns=['Interactor1','ppi','Interactor2'],header=['ID_interactor_A','ppi','ID_interactor_B'])


    @staticmethod
    def run(network=None, active_genes=None, output_folder=None, use_cache=true, slices_threshold=None, module_threshold=None, singularity=false):
        """
        Run DOMINO with Docker
        Let visualization always true, parallelization always 1
        @param network:  input network file (required)
        @param active_genes:  input active genes (required)
        @param output_folder: path to the output pathway file (required)
        @param use_cache: if True, use auto-generated cache network files (*.pkl) from previous executions with the same network (optional)
        @param slices_threshold: the threshold for considering a slice as relevant (optional)
        @param module_threshold: the threshold for considering a putative module as final module (optional)
        @param singularity: if True, run using the Singularity container instead of the Docker container (optional)
        """
        # Assuming defaults are: use_cache=true

        if not network or not active_genes or not output_folder:
            raise ValueError('Required DOMINO arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, node_file = prepare_volume(active_genes, work_dir)
        volumes.append(bind_path)

        bind_path, mapped_output_folder = prepare_volume(str(output_folder), work_dir)
        volumes.append(bind_path)

        ########

        bind_path, mapped_slices_file = prepare_volume(str(output_folder), work_dir)
        volumes.append(bind_path)

        # Make the slicer command to run within in the container
        slicer_command = ['slicer',
            '--network_file', network_file,
            '--output_file', mapped_slices_file]

        container_framework = 'singularity' if singularity else 'docker'
        slicer_out = run_container(container_framework,
                            'otjohnson/domino',
                            slicer_command,
                            volumes,
                            work_dir)
        print(slicer_out)

        ########


        # Makes the Python command to run within in the container
        command = ['domino',
                   '--active_genes_files', node_file,
                   '--network_file', network_file,
                   '--slices_file', slices_file,
                   '--output_folder', mapped_output_folder
                   '--parallelization, '1'
                   '--visualization', 'true']

        # Add optional arguments
        if use_cache is not true:
            command.extend(['-c', false])
        if slices_threshold is not None:
            command.extend(['-sth', str(slices_threshold)])
        if module_threshold is not None:
            command.extend(['-mth', str(slices_threshold)])

        print('Running DOMINO with arguments: {}'.format(' '.join(command)), flush=True)

        # container_framework = 'singularity' if singularity else 'docker'
        out = run_container(container_framework,
                            'otjohnson/domino',
                            command,
                            volumes,
                            work_dir)
        print(out)

        # delete modules.out
        # shutil library
        # append one html to end of another (argu)


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # edges dataframe
        # read html file
        with open(raw_pathway_file, 'r') as file:
            html = file.read()
            # for loop over lines of the file
                # if line starts with '      let data'
                     

        # Find the starting index of the line
        start_index = html.find('let data = [')
        # Find the ending index of the line
        end_index = html.find('];', start_index) + 1 # '+ 1' omits the semicolon

        # Extract the line as a string
        line = html[start_index:end_index]
        # remove beginning of the line to leave the json formatted string
        line2 = line.replace('let data = ', '')

        data = json.loads(line2)

        entries = []
        for entry in data:
            tmp = entry['data']
            entries.append(tmp)

        df = pd.DataFrame(entries)
        newDf = df.loc[:,['source', 'target']].dropna()
        
        # concatenate modules dataframe to bottom of outerloop data frame
        

        newDf['rank'] = 1 # adds in a rank column of 1s because the edges are not ranked

        newDf.to_csv(standardized_pathway_file, header=False, index=False)

