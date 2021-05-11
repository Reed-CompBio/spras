from src.PRM import PRM
import docker
from pathlib import Path
from src.util import prepare_path_docker
import os
import pandas as pd

__all__ = ['OmicsIntegrator1']


# TODO decide on default number of processes and threads
def write_conf(filename=Path('config.txt'), w=None, b=None, d=None, mu=None, noise=None, g=None, r=None):
    """
    Write the configuration file for Omics Integrator 1
    See https://github.com/fraenkel-lab/OmicsIntegrator#required-inputs
    filename: the name of the configuration file to write
    """
    if w is None or b is None or d is None:
        raise ValueError('Required Omics Integrator 1 configuration file arguments are missing')

    with open(filename, 'w') as f:
        f.write(f'w = {w}\n')
        f.write(f'b = {b}\n')
        f.write(f'D = {d}\n')
        if mu is not None:
            f.write(f'mu = {mu}\n')
        # Not supported
        #f.write('garnetBeta = 0.01\n')
        if noise is not None:
            f.write(f'noise = {noise}\n')
        if g is not None:
            f.write(f'g = {g}\n') # not the same as g in Omics Integrator 2
        if r is not None:
            f.write(f'r = {r}\n')
        f.write('processes = 1\n')
        f.write('threads = 1\n')


class OmicsIntegrator1(PRM):
    required_inputs = ['prizes', 'edges']

    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in OmicsIntegrator1.required_inputs:
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
            raise ValueError("Omics Integrator 1 requires node prizes or sources and targets")

        #Omics Integrator already gives warnings for strange prize values, so we won't here
        node_df.to_csv(filename_map['prizes'],sep='\t',index=False,columns=['NODEID','prize'],header=['name','prize'])

        #For now we assume all input networks are undirected until we expand how edge tables work
        edges_df = data.get_interactome()
        edges_df['directionality'] = 'U'
        edges_df.to_csv(filename_map['edges'],sep='\t',index=False,columns=['Interactor1','Interactor2','Weight','directionality'],header=['protein1','protein2','weight','directionality'])


    # TODO add parameter validation
    # TODO add support for knockout argument
    # TODO add reasonable default values
    # TODO document required arguments
    @staticmethod
    def run(edges=None, prizes=None, dummy_mode=None, mu_squared=None, exclude_terms=None,
            output_file=None, noisy_edges=None, shuffled_prizes=None, random_terminals=None,
            seed=None, w=None, b=None, d=None, mu=None, noise=None, g=None, r=None):
        """
        Run Omics Integrator 1 in the Docker image with the provided parameters.
        Does not support the garnet, cyto30, knockout, cv, or cv-reps arguments.
        The configuration file is generated from the provided arguments.
        Does not support the garnetBeta, processes, or threads configuration file parameters.
        The msgpath is not required because msgsteiner is available in the Docker image.
        Only the optimal forest sif file is retained.
        All other output files are deleted.
        @param output_file: the name of the output sif file for the optimal forest, which will overwrite any
        existing file with this name
        """
        if edges is None or prizes is None or output_file is None or w is None or b is None or d is None:
            raise ValueError('Required Omics Integrator 1 arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        work_dir = Path(__file__).parent.parent.absolute()

        edge_file = Path(edges)
        prize_file = Path(prizes)

        out_dir = Path(output_file).parent
        # Omics Integrator 1 requires that the output directory exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        conf_file = 'oi1-configuration.txt'
        conf_file_abs = Path(work_dir, conf_file)
        write_conf(conf_file_abs, w=w, b=b, d=d, mu=mu, noise=noise, g=g, r=r)

        command = ['python', '/OmicsIntegrator/scripts/forest.py',
                   '--edge', edge_file.as_posix(),
                   '--prize', prize_file.as_posix(),
                   '--conf', conf_file,
                   '--msgpath', '/OmicsIntegrator/msgsteiner-1.3/msgsteiner',
                   '--outpath', out_dir.as_posix(),
                   '--outlabel', 'oi1']

        # Add optional arguments
        if dummy_mode is not None:
            command.extend(['--dummyMode', str(dummy_mode)])
        if mu_squared is not None and mu_squared:
            command.extend(['--musquared'])
        if exclude_terms is not None and exclude_terms:
            command.extend(['--excludeTerms'])
        if noisy_edges is not None:
            command.extend(['--noisyEdges', str(noisy_edges)])
        if shuffled_prizes is not None:
            command.extend(['--shuffledPrizes', str(shuffled_prizes)])
        if random_terminals is not None:
            command.extend(['--randomTerminals', str(random_terminals)])
        if seed is not None:
            command.extend(['--seed', str(seed)])

        print('Running Omics Integrator 1 with arguments: {}'.format(' '.join(command)), flush=True)

        #Don't perform this step on systems where permissions aren't an issue like windows
        need_chown = True
        try:
            uid = os.getuid()
        except AttributeError:
            need_chown = False

        try:
            out = client.containers.run('reedcompbio/omics-integrator-1',
                                  command,
                                  stderr=True,
                                  volumes={prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator1', 'mode': 'rw'}},
                                  working_dir='/OmicsIntegrator1')
            if need_chown:
                #This command changes the ownership of output files so we don't
                # get a permissions error when snakemake tries to touch the files
                chown_command = " ".join(["chown",str(uid),out_dir.as_posix()+"/oi1*"])
                out_chown = client.containers.run('reedcompbio/omics-integrator-1',
                                      chown_command,
                                      stderr=True,
                                      volumes={prepare_path_docker(work_dir): {'bind': '/OmicsIntegrator1', 'mode': 'rw'}},
                                      working_dir='/OmicsIntegrator1')

            print(out.decode('utf-8'))
        finally:
            # Not sure whether this is needed
            client.close()
            conf_file_abs.unlink(missing_ok=True)

        # TODO do we want to retain other output files?
        # TODO if deleting other output files, write them all to a tmp directory and copy
        # the desired output file instead of using glob to delete files from the actual output directory
        # Rename the primary output file to match the desired output filename
        Path(output_file).unlink(missing_ok=True)
        output_sif = Path(out_dir, 'oi1_optimalForest.sif')
        output_sif.rename(output_file)
        # Remove the other output files
        for oi1_output in out_dir.glob('oi1_*'):
            oi1_output.unlink(missing_ok=True)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # I'm assuming from having read the documentation that we will be passing in optimalForest.sif
        # as raw_pathway_file, in which case the format should be edge1 interactiontype edge2.
        # if that assumption is wrong we will need to tweak things
        try:
            df = pd.read_csv(raw_pathway_file,sep='\s+', header=None)
        except pd.errors.EmptyDataError:
            with open(standardized_pathway_file,'w') as emptyFile:
                pass
            return
        df = df.take([0,2],axis=1)
        df[3] = [1 for _ in range(len(df.index))]
        df.to_csv(standardized_pathway_file, header=False,index=False,sep=' ')
