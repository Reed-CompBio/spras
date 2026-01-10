from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from spras.config.container_schema import ProcessedContainerSettings
from spras.config.util import CaseInsensitiveEnum
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Direction, GraphMultiplicity
from spras.interactome import reinsert_direction_col_mixed
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['DummyMode', 'OmicsIntegrator1', 'OmicsIntegrator1Params', 'write_conf']


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

class DummyMode(CaseInsensitiveEnum):
    terminals = 'terminals'
    "connect the dummy node to all nodes that have been assigned prizes"
    all = 'all'
    "connect the dummy node to all nodes in the interactome i.e. full set of nodes in graph"
    others = 'others'
    "connect the dummy node to all nodes that are not terminal nodes i.e. nodes w/o prizes"
    file = 'file'
    "connect the dummy node to a specific list of nodes provided in a file"

    # To make sure that DummyMode prints as `terminals`, etc.. in JSON dictionaries
    # (since they use object representation internally.)
    def __repr__(self) -> str:
        return f"'{self.name}'"

class OmicsIntegrator1Params(BaseModel):
    dummy_mode: Optional[DummyMode] = None
    mu_squared: bool = False
    exclude_terms: bool = False

    noisy_edges: int = 0
    "How many times you would like to add noise to the given edge values and re-run the algorithm."

    shuffled_prizes: int = 0
    "How many times the algorithm should shuffle the prizes and re-run"

    random_terminals: int = 0
    "How many times to apply the given prizes to random nodes in the interactome"

    seed: Optional[int] = None
    "The randomness seed to use."

    w: float
    "Float that affects the number of connected components, with higher values leading to more components"

    b: float
    "The trade-off between including more prizes and using less reliable edgess"

    d: int
    "Controls the maximum path-length from root to terminal nodes"

    mu: float = 0.0
    "Controls the degree-based negative prizes (default 0.0)"

    noise: Optional[float] = None
    "Standard Deviation of the gaussian noise added to edges in Noisy Edges Randomizations"

    g: float = 0.001
    "(gamma) msgsteiner reinforcement parameter that affects the convergence of the solution and runtime, with larger values leading to faster convergence but suboptimal results."

    r: float = 0
    "msgsteiner parameter that adds random noise to edges, which is rarely needed."

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

class OmicsIntegrator1(PRM[OmicsIntegrator1Params]):
    """
    Omics Integrator 1 works with partially directed graphs
    - it takes in the universal input directly

    Expected raw input format:
    Interactor1    Interactor2   Weight    Direction
    - the expected raw input file should have node pairs in the 1st and 2nd columns, with a weight in the 3rd column and
    directionality in the 4th column
    - it can include repeated and bidirectional edges
    - it uses 'U' for undirected edges and 'D' for directed edges

    """
    required_inputs = ['prizes', 'edges', 'dummy_nodes']
    dois = ["10.1371/journal.pcbi.1004879"]
    interactome_properties = [Direction.MIXED, GraphMultiplicity.SIMPLE]

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type. Associated files will be written with:
        - prizes: list of nodes associated with their prize
        - edges: list of edges associated with their weight and directionality
        - dummy_nodes: list of dummy nodes
        """
        OmicsIntegrator1.validate_required_inputs(filename_map)

        if data.contains_node_columns('prize'):
            # NODEID is always included in the node table
            node_df = data.get_node_columns(['prize'])
        elif data.contains_node_columns(['sources', 'targets']):
            # If there aren't prizes but are sources and targets, make prizes based on them
            node_df = data.get_node_columns(['sources','targets'])
            node_df.loc[node_df['sources']==True, 'prize'] = 1.0
            node_df.loc[node_df['targets']==True, 'prize'] = 1.0
        else:
            raise ValueError("Omics Integrator 1 requires node prizes or sources and targets")

        # Omics Integrator already gives warnings for strange prize values, so we won't here
        node_df.to_csv(filename_map['prizes'],sep='\t',index=False,columns=['NODEID','prize'],header=['name','prize'])

        # Get network file
        edges_df = data.get_interactome(OmicsIntegrator1.interactome_properties).df

        # Rename Direction column
        edges_df.to_csv(filename_map['edges'],sep='\t',index=False,
                        columns=['Interactor1','Interactor2','Weight','Direction'],
                        header=['protein1','protein2','weight','directionality'])

        # creates the dummy_nodes file
        if 'dummy' in data.node_table.columns:
            dummy_df = data.node_table[data.node_table['dummy'] == True]
            # save as list of dummy nodes
            dummy_df.to_csv(filename_map['dummy_nodes'], index=False, columns=['NODEID'], header=None)
        else:
            # create empty dummy file
            with open(filename_map['dummy_nodes'], mode='w'):
                pass

    # TODO add support for knockout argument
    # TODO add reasonable default values
    @staticmethod
    def run(inputs, output_file, args, container_settings=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        OmicsIntegrator1.validate_required_run_args(inputs, ["dummy_nodes"])

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, edge_file = prepare_volume(inputs["edges"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, prize_file = prepare_volume(inputs["prizes"], work_dir, container_settings)
        volumes.append(bind_path)

        # add dummy node file to the volume if dummy_mode is not None and it is 'file'
        dummy_file = None
        if args.dummy_mode == DummyMode.file:
            if "dummy_nodes" not in inputs:
                raise ValueError("dummy_nodes file is required when dummy_mode is set to 'file'")
            bind_path, dummy_file = prepare_volume(inputs["dummy_nodes"], work_dir, container_settings)
            volumes.append(bind_path)

        out_dir = Path(output_file).parent
        # Omics Integrator 1 requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir, container_settings)
        volumes.append(bind_path)

        conf_file = 'oi1-configuration.txt'
        conf_file_local = Path(out_dir, conf_file)
        # Temporary file that will be deleted after running Omics Integrator 1
        write_conf(conf_file_local, w=args.w, b=args.b, d=args.d, mu=args.mu,
                   noise=args.noise, g=args.g, r=args.r)
        bind_path, conf_file = prepare_volume(str(conf_file_local), work_dir, container_settings)
        volumes.append(bind_path)

        command = ['python', '/OmicsIntegrator/scripts/forest.py',
                   '--edge', edge_file,
                   '--prize', prize_file,
                   '--conf', conf_file,
                   '--msgpath', '/OmicsIntegrator/msgsteiner-1.3/msgsteiner',
                   '--outpath', mapped_out_dir,
                   '--outlabel', 'oi1']

        # add the dummy mode argument
        if args.dummy_mode is not None:
            # for custom dummy modes, add the file
            if dummy_file:
                command.extend(['--dummyMode', dummy_file])
            # else pass in the dummy_mode and let oi1 handle it
            else:
                command.extend(['--dummyMode', args.dummy_mode.value])

        # Add optional arguments
        if args.mu_squared:
            command.extend(['--musquared'])
        if args.exclude_terms:
            command.extend(['--excludeTerms'])
        command.extend(['--noisyEdges', str(args.noisy_edges)])
        command.extend(['--shuffledPrizes', str(args.shuffled_prizes)])
        command.extend(['--randomTerminals', str(args.random_terminals)])
        if args.seed is not None:
            command.extend(['--seed', str(args.seed)])

        container_suffix = "omics-integrator-1:v2"
        run_container_and_log('Omics Integrator 1',
                             container_suffix,
                             command,
                             volumes,
                             work_dir,
                             out_dir,
                             container_settings,
                             {'TMPDIR': mapped_out_dir})

        conf_file_local.unlink(missing_ok=True)

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
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        # I'm assuming from having read the documentation that we will be passing in optimalForest.sif
        # as raw_pathway_file, in which case the format should be edge1 interactiontype edge2.
        # if that assumption is wrong we will need to tweak things
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=None)
        if not df.empty:
            df.columns = ["Edge1", "InteractionType", "Edge2"]
            df = add_rank_column(df)
            df = reinsert_direction_col_mixed(df, "InteractionType", "pd", "pp")
            df.drop(columns=['InteractionType'], inplace=True)
            df.columns = ['Node1', 'Node2', 'Rank', 'Direction']
            df, has_duplicates = duplicate_edges(df)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")

        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
