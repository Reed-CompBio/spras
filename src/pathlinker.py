from src.PRM import PRM
import docker
import os
import warnings

__all__ = ['PathLinker']

class PathLinker(PRM):
    required_inputs = ['nodetypes.txt','network.txt']

    @staticmethod
    def generate_inputs(data, input_prefix, params):

        #Get sources and targets for node input file
        sources_targets = data.request_node_columns(["sources","targets"])
        if sources_targets is None:
            return False
        both_series = sources_targets.sources & sources_targets.targets
        for index,row in sources_targets[both_series].iterrows():
            warnMsg = row.NODEID+" has been labeled as both a source and a target."
            warnings.warn(warnMsg)

        #Create nodetype file
        input_df = sources_targets[["NODEID"]].copy()
        input_df.columns = ["#Node"]
        input_df.loc[sources_targets["sources"] == True,"Node type"]="source"
        input_df.loc[sources_targets["targets"] == True,"Node type"]="target"

        input_df.to_csv(input_prefix+"nodetypes.txt",sep="\t",index=False,columns=["#Node","Node type"])

        #This is pretty memory intensive. We might want to keep the interactome centralized.
        data.get_interactome().to_csv(input_prefix+"network.txt",sep="\t",index=False,columns=["Interactor1","Interactor2","Weight"])
        return True


    # Skips parameter validation step
    @staticmethod
    def run(output=None, input_pref=None, k=None):
        """
        Run PathLinker with Docker
        @param input_pref:  input directory prefix
        @param output: output directory
        @param k: path length (optional)
        """
        # Add additional parameter validation
        # Do not require k
        # Use the PathLinker default
        # Could consider setting the default here instead
        if not network or not input_pref or not output:
            raise ValueError('Required PathLinker arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        command = ['python', '../run.py']
        if k is not None:
            command.extend(['-k', str(k)])
        command.extend([network, nodes])
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
        # Temporarily create a placeholder output file
        with open(output, 'w') as out_file:
            out_file.write('PathLinker: run_static() command {}'.format(' '.join(command)))

    @staticmethod
    def parse_output():
        print('PathLinker: parseOutput()')
