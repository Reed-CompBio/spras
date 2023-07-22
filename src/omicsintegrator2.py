import os
from pathlib import Path

import docker
import pandas as pd

from src.prm import PRM
from src.util import prepare_path_docker

__all__ = ['OmicsIntegrator2']


class OmicsIntegrator2(PRM):
    required_inputs = ['prizes', 'edges']

    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in OmicsIntegrator2.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            #NODEID is always included in the node table
            node_df = data.request_node_columns(['prize'])
        elif data.contains_node_columns(['sources','targets']):
            #If there aren't prizes but are sources and targets, make prizes based on them
            node_df = data.request_node_columns(['sources','targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            raise ValueError("Omics Integrator 2 requires node prizes or sources and targets")

        #Omics Integrator already gives warnings for strange prize values, so we won't here
        node_df.to_csv(filename_map['prizes'],sep='\t',index=False,columns=['NODEID','prize'],header=['name','prize'])
        edges_df = data.get_interactome()

        #We'll have to update this when we make iteractomes more proper, but for now
        # assume we always get a weight and turn it into a cost.
        # use the same approach as omicsintegrator2 by adding half the max cost as the base cost.
        # if everything is less than 1 assume that these are confidences and set the max to 1
        edges_df['cost'] = (max(edges_df['Weight'].max(),1.0)*1.5) - edges_df['Weight']
        edges_df.to_csv(filename_map['edges'],sep='\t',index=False,columns=['Interactor1','Interactor2','cost'],header=['protein1','protein2','cost'])



    # TODO add parameter validation
    # TODO add reasonable default values
    # TODO document required arguments
    @staticmethod
    def run(edges=None, prizes=None, output_file=None, w=None, b=None, g=None, noise=None, noisy_edges=None,
            random_terminals=None, dummy_mode=None, seed=None, singularity=False):
        """
        Run Omics Integrator 2 in the Docker image with the provided parameters.
        Only the .tsv output file is retained and then renamed.
        All other output files are deleted.
        @param output_file: the name of the output file, which will overwrite any existing file with this name
        """
        if edges is None or prizes is None or output_file is None:
            raise ValueError('Required Omics Integrator 2 arguments are missing')

        if singularity:
            raise NotImplementedError('Omics Integrator 2 does not yet support Singularity')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        work_dir = Path(__file__).parent.parent.absolute()

        edge_file = Path(edges)
        prize_file = Path(prizes)

        out_dir = Path(output_file).parent
        # Omics Integrator 2 requires that the output directory exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        command = ['OmicsIntegrator', '-e', edge_file.as_posix(), '-p', prize_file.as_posix(),
                   '-o', out_dir.as_posix(), '--filename', 'oi2']

        # Add optional arguments
        if w is not None:
            command.extend(['-w', str(w)])
        if b is not None:
            command.extend(['-b', str(b)])
        if g is not None:
            command.extend(['-g', str(g)])
        if noise is not None:
            command.extend(['-noise', str(noise)])
        if noisy_edges is not None:
            command.extend(['--noisy_edges', str(noisy_edges)])
        if random_terminals is not None:
            command.extend(['--random_terminals', str(random_terminals)])
        if dummy_mode is not None:
            # This argument does not follow the other naming conventions
            command.extend(['--dummyMode', str(dummy_mode)])
        if seed is not None:
            command.extend(['--seed', str(seed)])

        print('Running Omics Integrator 2 with arguments: {}'.format(' '.join(command)), flush=True)

        #Don't perform this step on systems where permissions aren't an issue like windows
        need_chown = True
        try:
            uid = os.getuid()
        except AttributeError:
            need_chown = False

        try:
            out = client.containers.run('reedcompbio/omics-integrator-2',
                                        command,
                                        stderr=True,
                                        volumes={
                                            prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator2', 'mode': 'rw'}},
                                        working_dir='/OmicsIntegrator2')
            if need_chown:
                #This command changes the ownership of output files so we don't
                # get a permissions error when snakemake tries to touch the files
                chown_command = " ".join(["chown",str(uid),out_dir.as_posix()+"/oi2*"])
                client.containers.run('reedcompbio/omics-integrator-2',
                                            chown_command,
                                            stderr=True,
                                            volumes={prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator2', 'mode': 'rw'}},
                                            working_dir='/OmicsIntegrator2')

            print(out.decode('utf-8'))
        finally:
            # Not sure whether this is needed
            client.close()

        # TODO do we want to retain other output files?
        # TODO if deleting other output files, write them all to a tmp directory and copy
        # the desired output file instead of using glob to delete files from the actual output directory
        # Rename the primary output file to match the desired output filename
        Path(output_file).unlink(missing_ok=True)
        output_tsv = Path(out_dir, 'oi2.tsv')
        output_tsv.rename(output_file)
        # Remove the other output files
        for oi2_output in out_dir.glob('*.html'):
            oi2_output.unlink(missing_ok=True)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # Omicsintegrator2 returns a single line file if no network is found
        num_lines = sum(1 for line in open(raw_pathway_file))
        if num_lines < 2:
            with open(standardized_pathway_file, 'w'):
                pass
            return
        df = pd.read_csv(raw_pathway_file, sep='\t')
        df = df[df['in_solution'] == True]  # Check whether this column can be empty before revising this line
        df = df.take([0, 1], axis=1)
        df[3] = [1 for _ in range(len(df.index))]
        df.to_csv(standardized_pathway_file, header=False, index=False, sep='\t')
