from pathlib import Path

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import MissingDataError
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import (
    add_rank_column,
    duplicate_edges,
    raw_pathway_df,
)

__all__ = ['BowTieBuilder']

"""
BTB will construct a BowTie-shaped graph from the provided input file.
BTB works with directed and undirected graphs.
It generates a graph connecting multiple source nodes to multiple target nodes with the minimal number of intermediate nodes as possible.

Expected raw edge file format:
Interactor1     Interactor2     Weight
"""

class BowTieBuilder(PRM):
    required_inputs = ['sources', 'targets', 'edges']
    dois = ["10.1186/1752-0509-3-67"]

    #generate input taken from meo.py because they have same input requirements
    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        BowTieBuilder.validate_required_inputs(filename_map)

        # Get sources and write to file, repeat for targets
        # Does not check whether a node is a source and a target
        for node_type, nodes in data.get_node_columns_separate(['sources', 'targets'], "BowTieBuilder").items():
            # TODO test whether this selection is needed, what values could the column contain that we would want to
            # include or exclude?
            nodes = nodes.loc[nodes[node_type]]
            nodes.to_csv(filename_map[node_type], sep='\t', index=False, columns=['NODEID'], header=False)

        # Create network file
        edges = data.get_interactome()

        # Format into directed graph (BTB uses the nx.DiGraph constructor internally)
        edges = convert_undirected_to_directed(edges)

        edges.to_csv(filename_map["edges"], sep="\t", index=False,
                                      columns=["Interactor1", "Interactor2", "Weight"],
                                      header=False)



    # Skips parameter validation step
    @staticmethod
    def run(sources=None, targets=None, edges=None, output_file=None, container_framework="docker"):
        """
        Run BTB with Docker
        @param sources:  input source file (required)
        @param targets:  input target file (required)
        @param edges:    input edge file (required)
        @param output_file: path to the output pathway file (required)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """

        # Tests for pytest (docker container also runs this)
        # Testing out here avoids the trouble that container errors provide

        if not sources or not targets or not edges or not output_file:
            raise ValueError('Required BowTieBuilder arguments are missing')

        if not Path(sources).exists() or not Path(targets).exists() or not Path(edges).exists():
            raise ValueError('Missing input file')

        # Testing for btb index errors
        # TODO: This error will never actually occur if the inputs are passed through
        # `generate_inputs`. See the discussion about removing this or making this a habit at
        # https://github.com/Reed-CompBio/spras/issues/306.
        with open(edges, 'r') as edge_file:
            try:
                for line in edge_file:
                    line = line.strip().split('\t')[2]

            except Exception as err:
                # catches a much harder to debug error in BTB.
                raise IndexError("BTB edges are not formatted correctly") from err

        work_dir = '/btb'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, source_file = prepare_volume(sources, work_dir)
        volumes.append(bind_path)

        bind_path, target_file = prepare_volume(targets, work_dir)
        volumes.append(bind_path)

        bind_path, edges_file = prepare_volume(edges, work_dir)
        volumes.append(bind_path)

        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/raw-pathway.txt'  # Use posix path inside the container

        command = ['python',
                   'btb.py',
                   '--edges',
                   edges_file,
                   '--sources',
                   source_file,
                   '--targets',
                   target_file,
                   '--output_file',
                   mapped_out_prefix]

        container_suffix = "bowtiebuilder:v2"
        run_container_and_log(
            'BowTieBuilder',
            container_framework,
            container_suffix,
            command,
            volumes,
            work_dir,
            out_dir)
        # Output is already written to raw-pathway.txt file


    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # TODO: consider using multiple raw_pathway_files
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=0)
        if not df.empty:
            df = add_rank_column(df)
            df = reinsert_direction_col_directed(df)
            df.columns = ['Node1', 'Node2', 'Rank', 'Direction']
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
        df.to_csv(standardized_pathway_file, index=False, sep='\t', header=True)
