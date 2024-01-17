import json
from pathlib import Path

import pandas as pd

from spras.containers import prepare_volume, run_container
from spras.interactome import (
    add_constant,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM

__all__ = ['DOMINO', 'pre_domino_id_transform', 'post_domino_id_transform']

ID_PREFIX = 'ENSG0'
ID_PREFIX_LEN = len(ID_PREFIX)


"""
DOMINO will construct a fully undirected graph from the provided input file
- in the algorithm, it uses nx.Graph()

Expected raw input format:
Interactor1     ppi     Interactor2
- the expected raw input file should have node pairs in the 1st and 3rd columns, with a 'ppi' in the 2nd column
- it can include repeated and bidirectional edges
"""
class DOMINO(PRM):
    required_inputs = ['network', 'active_genes']

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        @return:
        """
        for input_type in DOMINO.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # Get active genes for node input file
        if data.contains_node_columns('active'):
            # NODEID is always included in the node table
            node_df = data.request_node_columns(['active'])
        else:
            raise ValueError('DOMINO requires active genes')
        node_df = node_df[node_df['active'] == True]

        # Transform each node id with a prefix
        node_df['NODEID'] = node_df['NODEID'].apply(pre_domino_id_transform)

        # Create active_genes file
        node_df.to_csv(filename_map['active_genes'], sep='\t', index=False, columns=['NODEID'], header=False)

        # Create network file
        edges_df = data.get_interactome()

        # Format network file
        # edges_df = convert_directed_to_undirected(edges_df)
        # - technically this can be called but since we don't use the column and based on what the function does, it is not truly needed
        edges_df = add_constant(edges_df, 'ppi', 'ppi')

        # Transform each node id with a prefix
        edges_df['Interactor1'] = edges_df['Interactor1'].apply(pre_domino_id_transform)
        edges_df['Interactor2'] = edges_df['Interactor2'].apply(pre_domino_id_transform)

        edges_df.to_csv(filename_map['network'], sep='\t', index=False, columns=['Interactor1', 'ppi', 'Interactor2'],
                        header=['ID_interactor_A', 'ppi', 'ID_interactor_B'])

    @staticmethod
    def run(network=None, active_genes=None, output_file=None, slice_threshold=None, module_threshold=None, container_framework="docker"):
        """
        Run DOMINO with Docker.
        Let visualization be always true, parallelization be always 1 thread, and use_cache be always false.
        DOMINO produces multiple output module files in an HTML format. SPRAS concatenates these files into one file.
        @param network: input network file (required)
        @param active_genes: input active genes (required)
        @param output_file: path to the output pathway file (required)
        @param slice_threshold: the p-value threshold for considering a slice as relevant (optional)
        @param module_threshold: the p-value threshold for considering a putative module as final module (optional)
        @param container_framework: choose the container runtime framework, currently supports "docker" or "singularity" (optional)
        """

        if not network or not active_genes or not output_file:
            raise ValueError('Required DOMINO arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (source, destination)
        volumes = list()

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, node_file = prepare_volume(active_genes, work_dir)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)

        slices_file = Path(out_dir, 'slices.txt')
        bind_path, mapped_slices_file = prepare_volume(str(slices_file), work_dir)
        volumes.append(bind_path)

        # Make the Python command to run within the container
        slicer_command = ['slicer',
                          '--network_file', network_file,
                          '--output_file', mapped_slices_file]

        print('Running slicer with arguments: {}'.format(' '.join(slicer_command)), flush=True)

        container_suffix = "domino"
        slicer_out = run_container(container_framework,
                                   container_suffix,
                                   slicer_command,
                                   volumes,
                                   work_dir)
        print(slicer_out)

        # Make the Python command to run within the container
        domino_command = ['domino',
                          '--active_genes_files', node_file,
                          '--network_file', network_file,
                          '--slices_file', mapped_slices_file,
                          '--output_folder', mapped_out_dir,
                          '--use_cache', 'false',
                          '--parallelization', '1',
                          '--visualization', 'true']

        # Add optional arguments
        if slice_threshold is not None:
            # DOMINO readme has the wrong argument https://github.com/Shamir-Lab/DOMINO/issues/12
            domino_command.extend(['--slice_threshold', str(slice_threshold)])
        if module_threshold is not None:
            domino_command.extend(['--module_threshold', str(module_threshold)])

        print('Running DOMINO with arguments: {}'.format(' '.join(domino_command)), flush=True)

        domino_out = run_container(container_framework,
                                   container_suffix,
                                   domino_command,
                                   volumes,
                                   work_dir)
        print(domino_out)

        # DOMINO creates a new folder in out_dir to output its modules HTML files into called active_genes
        # The filename is determined by the input active_genes and cannot be configured
        # Leave these HTML files for user inspection
        out_modules_dir = Path(out_dir, 'active_genes')

        # Concatenate each produced module HTML file into one file
        with open(output_file, 'w') as fo:
            for html_file in out_modules_dir.glob('module_*.html'):
                with open(html_file, 'r') as fi:
                    fo.write(fi.read())

        # Clean up DOMINO intermediate and pickle files
        slices_file.unlink(missing_ok=True)
        Path(out_dir, 'network.slices.pkl').unlink(missing_ok=True)
        Path(network + '.pkl').unlink(missing_ok=True)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert the merged HTML modules into the universal pathway format
        @param raw_pathway_file: the merged HTML modules file
        @param standardized_pathway_file: the edges from the modules written in the universal format
        """
        edges_df = pd.DataFrame()

        with open(raw_pathway_file, 'r') as file:
            for line in file:
                clean_line = line.strip()
                # The pattern in the HTML that indicates the JSON data
                if clean_line.startswith('let data = ['):
                    clean_line = clean_line.replace('let data = ', '')  # Start of the line
                    clean_line = clean_line.replace(';', '')  # End of the line

                    data = json.loads(clean_line)

                    entries = []
                    # Iterate over the JSON entries, which contain both node information and edge information
                    for entry in data:
                        entries.append(entry['data'])

                    # Create a dataframe with all the data from the JSON row, keep only the source and target
                    # columns that indicate edges
                    # Dropping the other rows eliminates the node information
                    module_df = pd.DataFrame(entries)
                    module_df = module_df.loc[:, ['source', 'target']].dropna()

                    # Add the edges from this module to the cumulative pathway edges
                    edges_df = pd.concat([edges_df, module_df], axis=0)

        # DOMINO produces empty output files in some settings such as when it is run with small input files
        # and generates a ValueError
        if len(edges_df) > 0:
            edges_df['rank'] = 1  # Adds in a rank column of 1s because the edges are not ranked

            # Remove the prefix
            edges_df['source'] = edges_df['source'].apply(post_domino_id_transform)
            edges_df['target'] = edges_df['target'].apply(post_domino_id_transform)
            edges_df = reinsert_direction_col_undirected(edges_df)

        edges_df.to_csv(standardized_pathway_file, sep='\t', header=False, index=False)


def pre_domino_id_transform(node_id):
    """
    DOMINO requires module edges to have the 'ENSG0' string as a prefix for visualization.
    Prepend each node id with this ID_PREFIX.
    @param node_id: the node id to transform
    @return the node id with the prefix added
    """
    return ID_PREFIX + node_id


def post_domino_id_transform(node_id):
    """
    Remove ID_PREFIX from the beginning of the node id if it is present.
    @param node_id: the node id to transform
    @return the node id without the prefix, if it was present, otherwise the original node id
    """
    # Use removeprefix if SPRAS ever requires Python >= 3.9
    # https://docs.python.org/3/library/stdtypes.html#str.removeprefix
    if node_id.startswith(ID_PREFIX):
        return node_id[ID_PREFIX_LEN:]
    else:
        return node_id
