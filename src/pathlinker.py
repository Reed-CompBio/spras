import docker
import os
import sys
import warnings
import tempfile
from src.PRM import PRM
from pathlib import Path
from src.util import prepare_path_docker
from shutil import copy, rmtree, copytree

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
        data.get_interactome().to_csv(filename_map["network"],sep="\t",index=False,columns=["Interactor1","Interactor2","Weight"])


    # Skips parameter validation step
    @staticmethod
    def run(nodetypes = None, network = None, output_dir=None, k=None):
        """
        Run PathLinker with Docker
        @param nodetypes:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_dir: path to the output pathway directory (required)
        @param k: path length (optional)
        """
        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not nodetypes or not network or not output_dir:
            raise ValueError('Required PathLinker arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()

        # work dir set as the root of the repository
        work_dir = Path(__file__).parent.parent.absolute()
        print(f"current working dir: {work_dir}")

        # create path objects for input files
        node_file = Path(nodetypes)
        network_file = Path(network)

        # store output dir for volume mounts
        out_dir = Path(output_dir).absolute()

        # assert output dir exists
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)

        # create temp directory for input files
        dir_path = tempfile.mkdtemp()
        files = [network_file, node_file]
        for file in files:
            copy(file, dir_path)
        
        command = ['python', '../run.py', '/home/files/'+os.path.basename(network_file), 
                        '/home/files/'+os.path.basename(node_file)]
        if k is not None:
            command.extend(['-k', str(k)])

        try:
            # mount 2 volumes
            #   tempdir : /home/files
            #   output dir (on disk) : /home/out
            # call pathlinker from /home/out dir 
            container_output = client.containers.run(
                'reedcompbio/pathlinker',
                command,
                stderr=True,
                volumes={
                    prepare_path_docker(Path(dir_path)): {'bind': '/home/files', 'mode': 'rw'},
                    prepare_path_docker(out_dir): {'bind': '/home/out', 'mode': 'rw'}
                },
                working_dir='/home/out'
            )
            print(container_output.decode('utf-8'))

        finally:
            # Not sure whether this is needed
            client.close()
            rmtree(dir_path)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # TODO update the parse_output command to translate and write the pathway file
        # Temporarily create a placeholder output file for Snakemake
        with open(standardized_pathway_file, 'w') as out_file:
            out_file.write(f'PathLinker converting raw pathway {raw_pathway_file}')
