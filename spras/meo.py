from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    add_directionality_constant,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import add_rank_column

__all__ = ['MEO', 'write_properties']


# Only supports the Random orientation algorithm
# Does not support MINSAT or MAXCSP
# TODO add parameter validation
def write_properties(filename=Path('properties.txt'), edges=None, sources=None, targets=None, edge_output=None,
                     path_output=None, max_path_length=None, local_search=None, rand_restarts=None):
    """
    Write the properties file for Maximum Edge Orientation
    See https://github.com/agitter/meo/blob/master/sample.props for property descriptions and the default values at
    https://github.com/agitter/meo/blob/master/src/alg/EOMain.java#L185-L199
    All file and directory names, except the filename argument, should be converted to container-friendly filenames with
    util.prepare_volume before passing them to this function
    filename: the name of the properties file to write on the local file system
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


"""
MEO can support partially directed graphs

Expected raw input format:
Interactor1   pp/pd   Interactor2   Weight
- the expected raw input file should have node pairs in the 1st and 3rd columns, with a directionality in the 2nd column and the weight in the 4th column
- it use pp for undirected edges and pd for directed edges
- it cannot include repeated and directed edges in opposite directions (A->B and B->A in the input)
- MEO assumes that it should be an undirected edge instead
- it cannot support undirected self edges (A-A)

- MEO tracks the directionality of the original edges, but all of its output edges are directed.
- To remain accurate to MEO's design we will also treat the output graph's as directed
"""
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

        # Create network file
        edges = data.get_interactome()

        # Format network file
        edges = add_directionality_constant(edges, 'EdgeType', '(pd)', '(pp)')

        edges.to_csv(filename_map['edges'], sep='\t', index=False,
                     columns=['Interactor1', 'EdgeType', 'Interactor2', 'Weight'], header=False)


    # TODO add parameter validation
    # TODO document required arguments
    @staticmethod
    def run(edges=None, sources=None, targets=None, output_file=None, max_path_length=None, local_search=None,
            rand_restarts=None, container_framework="docker"):
        """
        Run Maximum Edge Orientation in the Docker image with the provided parameters.
        The properties file is generated from the provided arguments.
        Only supports the Random orientation algorithm.
        Does not support MINSAT or MAXCSP.
        Only the edge output file is retained.
        All other output files are deleted.
        @param output_file: the name of the output edge file, which will overwrite any existing file with this name
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """
        if edges is None or sources is None or targets is None or output_file is None:
            raise ValueError('Required Maximum Edge Orientation arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, edge_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        bind_path, source_file = prepare_volume(sources, work_dir)
        volumes.append(bind_path)

        bind_path, target_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        # Maximum Edge Orientation requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)

        bind_path, mapped_output_file = prepare_volume(str(output_file), work_dir)
        volumes.append(bind_path)

        # Hard code the path output filename, which will be deleted
        path_output_file = Path(out_dir, 'path-output.txt')
        bind_path, mapped_path_output = prepare_volume(str(path_output_file), work_dir)
        volumes.append(bind_path)

        properties_file = 'meo-properties.txt'
        properties_file_local = Path(out_dir, properties_file)
        write_properties(filename=properties_file_local, edges=edge_file, sources=source_file, targets=target_file,
                         edge_output=mapped_output_file, path_output=mapped_path_output,
                         max_path_length=max_path_length, local_search=local_search, rand_restarts=rand_restarts)
        bind_path, properties_file = prepare_volume(str(properties_file_local), work_dir)
        volumes.append(bind_path)

        command = ['java', '-jar', '/meo/EOMain.jar', properties_file]

        print('Running Maximum Edge Orientation with arguments: {}'.format(' '.join(command)), flush=True)

        container_suffix = "meo"
        out = run_container(container_framework,
                            container_suffix,
                            command,
                            volumes,
                            work_dir)
        print(out)

        properties_file_local.unlink(missing_ok=True)

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
        df = add_rank_column(df)
        df = reinsert_direction_col_directed(df)

        df.to_csv(standardized_pathway_file, columns=['Source', 'Target', 'Rank', "Direction"], header=False,
                  index=False, sep='\t')
