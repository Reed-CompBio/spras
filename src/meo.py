from src.PRM import PRM
import docker
from pathlib import Path
from src.util import prepare_path_docker
import os
import pandas as pd

__all__ = ['MEO']


# Only supports the Random orientation algorithm
# Does not support MINSAT or MAXCSP
# TODO add parameter validation
def write_properties(filename=Path('properties.txt'), edges=None, sources=None, targets=None, edge_output=None,
                     path_output=None, max_path_length=None, local_search=None, rand_restarts=None):
    """
    Write the properties file for Maximum Edge Orientation
    See https://github.com/agitter/meo/blob/master/sample.props for property descriptions and the default values at
    https://github.com/agitter/meo/blob/master/src/alg/EOMain.java#L185-L199
    filename: the name of the properties file to write
    """
    if edges is None or sources is None or targets is None or edge_output is None or path_output is None:
        raise ValueError('Required Maximum Edge Orientation properties file arguments are missing')

    with open(filename, 'w') as f:
        # Write the required properties
        f.write(f'edges.file = {Path(edges).as_posix()}\n')
        f.write(f'sources.file = {Path(sources).as_posix()}\n')
        f.write(f'targets.file = {Path(targets).as_posix()}\n')
        f.write(f'edge.output.file = {Path(edge_output).as_posix()}\n')
        f.write(f'path.output.file = {Path(path_output).as_posix()}\n')

        # Write the optional properties if they were specified
        if max_path_length is not None:
            f.write(f'max.path.length = {max_path_length}\n')
        if local_search is not None:
            f.write(f'local.search = {local_search}\n')
        if rand_restarts is not None:
            f.write(f'rand.restarts = {rand_restarts}\n')

        # Write the hard-coded properties
        f.write(f'alg = Random\n')

        # Do not need csp.phase, csp.gen.file, or csp.sol.file because MAXCSP is not supported


class MEO(PRM):
    required_inputs = ['sources', 'targets', 'edges']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in MEO.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # Get sources and write to file, repeat for targets
        # Does not check whether a node is a source and a target
        for node_type in ['sources', 'targets']:
            nodes = data.request_node_columns([node_type])
            if nodes is None:
                raise ValueError(f'No {node_type} found in the node files')

            # TODO test whether this selection is needed, what values could the column contain that we would want to
            # include or exclude?
            nodes = nodes.loc[nodes[node_type]]
            nodes.to_csv(filename_map[node_type], index=False, columns=['NODEID'], header=False)

        # TODO need to support partially directed graphs
        # Expected columns are Node1 EdgeType Node2 Weight
        edges = data.get_interactome()
        # For now all edges are undirected
        edges.insert(1, 'EdgeType', '(pp)')
        edges.to_csv(filename_map['edges'], sep='\t', index=False, columns=['Interactor1', 'EdgeType', 'Interactor2', 'Weight'], header=False)


    # TODO add parameter validation
    # TODO document required arguments
    @staticmethod
    def run(edges=None, sources=None, targets=None, output_file=None, max_path_length=None, local_search=None,
            rand_restarts=None):
        """
        Run Maximum Edge Orientation in the Docker image with the provided parameters.
        The properties file is generated from the provided arguments.
        Only supports the Random orientation algorithm.
        Does not support MINSAT or MAXCSP.
        Only the edge output file is retained.
        All other output files are deleted.
        @param output_file: the name of the output edge file, which will overwrite any existing file with this name
        """
        if edges is None or sources is None or targets is None or output_file is None:
            raise ValueError('Required Maximum Edge Orientation arguments are missing')

        # Initialize a Docker client using environment variables
        client = docker.from_env()
        work_dir = Path(__file__).parent.parent.absolute()

        out_dir = Path(output_file).parent
        # Maximum Edge Orientation requires that the output directory exist
        Path(work_dir, out_dir).mkdir(parents=True, exist_ok=True)
        # Hard code the path output filename, which will be deleted
        # TODO use a tmp file
        path_output_file = Path(out_dir, 'path-output.txt')

        properties_file = 'meo-properties.txt'
        properties_file_abs = Path(work_dir, properties_file)
        write_properties(filename=properties_file_abs, edges=edges, sources=sources, targets=targets,
                         edge_output=output_file, path_output=path_output_file,
                         max_path_length=max_path_length, local_search=local_search, rand_restarts=rand_restarts)

        command = [properties_file]

        print('Running Maximum Edge Orientation with arguments: {}'.format(' '.join(command)), flush=True)

        # Don't perform this step on systems where permissions aren't an issue like windows
        need_chown = True
        try:
            uid = os.getuid()
        except AttributeError:
            need_chown = False

        try:
            out = client.containers.run('reedcompbio/meo',
                                  command,
                                  stderr=True,
                                  volumes={prepare_path_docker(work_dir): {'bind': '/spras', 'mode': 'rw'}},
                                  working_dir='/spras')
            if need_chown:
                # This command changes the ownership of output files so we don't
                # get a permissions error when snakemake tries to touch the files
                chown_command = " ".join([str(uid), output_file, path_output_file.as_posix()])
                # Modify the entrypoint because the command is expected to be a properties file that is passed
                # to the jar file
                client.containers.run('reedcompbio/meo',
                                      chown_command,
                                      stderr=True,
                                      volumes={prepare_path_docker(work_dir): {'bind': '/spras', 'mode': 'rw'}},
                                      working_dir='/spras',
                                      entrypoint='/bin/chown')

            print(out.decode('utf-8'))
        finally:
            # Not sure whether this is needed
            client.close()
            properties_file_abs.unlink(missing_ok=True)

        # TODO do we want to retain other output files?
        # TODO if deleting other output files, write them all to a tmp directory and copy
        # the desired output file instead of using glob to delete files from the actual output directory
        path_output_file.unlink(missing_ok=False)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # Columns Source Type Target Oriented Weight
        df = pd.read_csv(raw_pathway_file, sep='\t')
        # Keep only edges that were assigned an orientation (direction)
        df = df.loc[df['Oriented']]
        # TODO what should be the edge rank?
        # Would need to load the paths output file to rank edges correctly
        df.insert(5, 'Rank', 1)  # Add a constant rank of 1
        # TODO switch to tab-delimited once other methods are changed
        df.to_csv(standardized_pathway_file, columns=['Source', 'Target', 'Rank'], header=False, index=False, sep=' ')
