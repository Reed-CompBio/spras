import docker
import os
import sys
import pandas as pd
import warnings
from src.PRM import PRM
from pathlib import Path
from src.util import prepare_path_docker

__all__ = ['PathLinker']

class PathLinker(PRM):
    required_inputs = ['nodetypes', 'network']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in PathLinker.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        #Get sources and targets for node input file
        sources_targets = data.request_node_columns(["sources", "targets"])
        if sources_targets is None:
            return False
        both_series = sources_targets.sources & sources_targets.targets
        for index,row in sources_targets[both_series].iterrows():
            warn_msg = row.NODEID+" has been labeled as both a source and a target."
            warnings.warn(warn_msg)

        #Create nodetype file
        input_df = sources_targets[["NODEID"]].copy()
        input_df.columns = ["#Node"]
        input_df.loc[sources_targets["sources"] == True,"Node type"]="source"
        input_df.loc[sources_targets["targets"] == True,"Node type"]="target"

        input_df.to_csv(filename_map["nodetypes"],sep="\t",index=False,columns=["#Node","Node type"])

        #This is pretty memory intensive. We might want to keep the interactome centralized.
        data.get_interactome().to_csv(filename_map["network"],sep="\t",index=False,columns=["Interactor1","Interactor2","Weight"],header=["#Interactor1","Interactor2","Weight"])


    # Skips parameter validation step
    @staticmethod
    def run(nodetypes=None, network=None, output_file=None, k=None):
        """
        Run PathLinker with Docker
        @param nodetypes:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_file: path to the output pathway file (required)
        @param k: path length (optional)
        """
        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not nodetypes or not network or not output_file:
            raise ValueError('Required PathLinker arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()

        # work dir set as the root of the repository
        work_dir = Path(__file__).parent.parent.absolute()

        # create path objects for input files
        node_file = Path(nodetypes)
        network_file = Path(network)

        out_dir = Path(output_file).parent
        # When renaming the output file, the output directory must already exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        command = ['python', '/PathLinker/run.py', '/home/spras/'+network_file.as_posix(), 
                        '/home/spras/'+node_file.as_posix()]

        # Add optional argument
        if k is not None:
            command.extend(['-k', str(k)])

        #Don't perform this step on systems where permissions aren't an issue like windows
        need_chown = True
        try:
            uid = os.getuid()
        except AttributeError:
            need_chown = False

        try:
            container_output = client.containers.run(
                'reedcompbio/pathlinker',
                command,
                stderr=True,
                volumes={
                    prepare_path_docker(work_dir): {'bind': '/home/spras', 'mode': 'rw'}
                },
                working_dir='/home/spras/')
            print(container_output.decode('utf-8'))
            if need_chown:
                #This command changes the ownership of output files so we don't
                # get a permissions error when snakemake tries to touch the files
                # PathLinker writes output files to the working directory
                chown_command = " ".join(['chown',str(uid),'./out*-ranked-edges.txt'])
                client.containers.run('reedcompbio/pathlinker',
                                      chown_command,
                                      stderr=True,
                                      volumes={prepare_path_docker(work_dir): {'bind': '/home/spras', 'mode': 'rw'}},
                                      working_dir='/home/spras/')

        finally:
            # Not sure whether this is needed
            client.close()

        # Rename the primary output file to match the desired output filename
        # Currently PathLinker only writes one output file so we do not need to delete others
        Path(output_file).unlink(missing_ok=True)
        # We may not know the value of k that was used
        output_edges = Path(next(work_dir.glob('out*-ranked-edges.txt')))
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # Questions: should there be a header/optional columns?
        # What about multiple raw_pathway_files
        # We should not allow spaces in the node names if we use space separator.
        df = pd.read_csv(raw_pathway_file,sep='\t').take([0,1,2],axis=1)
        df.to_csv(standardized_pathway_file, header=False,index=False,sep=' ')
