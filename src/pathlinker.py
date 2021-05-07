from src.PRM import PRM
import docker
import os
import warnings

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
    def run(nodetypes = None, network = None, output_file=None, k=None):
        """
        Run PathLinker with Docker
        @param nodetypes:  input node types with sources and targets (required)
        @param network:  input network file (required)
        @param output_file: path to the output pathway file (required)
        @param k: path length (optional)
        """

        # TODO update the run command to use the new arguments provided and write the pathway to output_file
        # Temporarily create a placeholder output file for Snakemake
        with open(output_file, 'w') as out_file:
            out_file.write('PathLinker: run arguments {}'.format(' '.join([nodetypes, network, output_file, str(k)])))
        return

        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not nodetypes or not network or not output_file:
            raise ValueError('Required PathLinker arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        command = ['python', '../run.py']
        if k is not None:
            command.extend(['-k', str(k)])
        # Currently broken
        #command.extend([network, nodes])
        print('PathLinker: run_static() command {}'.format(' '.join(command)))

        working_dir = os.getcwd()

        data_dir = os.path.join(working_dir, 'docker', 'pathlinker')
        # Tony can run this example successfully on Git for Windows even with the following lines commented out
        if os.name == 'nt':
            print("running on Windows")
            data_dir = str(data_dir).replace("\\", "/").replace("C:", "//c")

        try:
            container_output = client.containers.run('ajshedivy/pr-pathlinker:example',
                                command,
                                stderr=True,
                                volumes={data_dir: {'bind': '/home/PathLinker/data', 'mode': 'rw'}},
                                working_dir='/home/PathLinker'
                                )
            print(container_output.decode('utf-8'))

        finally:
            # Not sure whether this is needed
            client.close()

        # Need to rename the output file to match the specific output file in the params


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
