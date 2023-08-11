import json
from pathlib import Path

import pandas as pd

from src.prm import PRM
from src.util import prepare_volume, run_container

__all__ = ['DOMINO']

ID_PREFIX = 'ENSG0'


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
            raise ValueError("DOMINO requires active genes")
        node_df = node_df[node_df['active'] == True]

        # transform each node id with a prefix
        node_df['NODEID'] = node_df['NODEID'].apply(pre_domino_id_transform)
        # e.g., ENSG0[node_id]

        # Create active_genes file
        node_df.to_csv(filename_map['active_genes'],sep="\t",index=False,columns=['NODEID'], header=False)

        # Create network file
        edges_df = data.get_interactome()
        edges_df['ppi'] = 'ppi'

        # Transform each node id with a prefix
        edges_df['Interactor1'] = edges_df['Interactor1'].apply(pre_domino_id_transform)
        edges_df['Interactor2'] = edges_df['Interactor2'].apply(pre_domino_id_transform)

        edges_df.to_csv(filename_map['network'], sep='\t', index=False, columns=['Interactor1', 'ppi', 'Interactor2'],
                        header=['ID_interactor_A', 'ppi', 'ID_interactor_B'])

    @staticmethod
    def run(network=None, active_genes=None, output_file=None, use_cache=True, slices_threshold=None, module_threshold=None, singularity=False):
        """
        Run DOMINO with Docker
        Let visualization be always true, parallelization be always 1 thread
        DOMINO produces multiple output module files in an HTML format. SPRAS concatenates these files into one file,
        which from which it will extract edges from to produce one pathway.
        @param network:  input network file (required)
        @param active_genes:  input active genes (required)
        @param output_file: path to the output pathway file (required)
        @param use_cache: if True, use auto-generated cache network files (*.pkl) from previous executions with the same network (optional)
        @param slices_threshold: the p-value threshold for considering a slice as relevant (optional)
        @param module_threshold: the p-value threshold for considering a putative module as final module (optional)
        @param singularity: if True, run using the Singularity container instead of the Docker container (optional)
        """
        # Assuming defaults are: use_cache=true

        if not network or not active_genes or not output_file:
            raise ValueError('Required DOMINO arguments are missing')

        work_dir = '/spras'

        # Each volume is a tuple (source, destination)
        volumes = list()

        bind_path, network_file = prepare_volume(network, work_dir)
        volumes.append(bind_path)

        bind_path, node_file = prepare_volume(active_genes, work_dir)
        volumes.append(bind_path)

        # Use its --output_folder argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)

        bind_path, mapped_slices_dir = prepare_volume('slices.txt', work_dir)
        volumes.append(bind_path)
        # /spras/ADFJGFD/slices.txt

        slicer_command = ['slicer',
                          '--network_file', network_file,
                          '--output_file', mapped_slices_dir]

        print('Running slicer with arguments: {}'.format(' '.join(slicer_command)), flush=True)

        container_framework = 'singularity' if singularity else 'docker'
        slicer_out = run_container(container_framework,
                                   'otjohnson/domino',
                                   slicer_command,
                                   volumes,
                                   work_dir)
        print(slicer_out)

        # Make the Python command to run within the container
        command = ['domino',
                   '--active_genes_files', node_file,
                   '--network_file', network_file,
                   '--slices_file', mapped_slices_dir,
                   '--output_folder', mapped_out_dir,
                   '--parallelization', '1',
                   '--visualization', 'true']

        # Add optional arguments
        if use_cache is not True:
            command.extend(['-c', 'false'])
        if slices_threshold is not None:
            command.extend(['-sth', str(slices_threshold)])
        if module_threshold is not None:
            command.extend(['-mth', str(module_threshold)])

        print('Running DOMINO with arguments: {}'.format(' '.join(command)), flush=True)

        # container_framework = 'singularity' if singularity else 'docker'
        domino_out = run_container(container_framework,
                                   'otjohnson/domino',
                                   command,
                                   volumes,
                                   work_dir)
        print(domino_out)

        # DOMINO creates a new folder in out_dir to output its modules files into /active_genes
        out_modules_dir = Path(out_dir, 'active_genes')
        #Path(out_modules_dir, 'modules.out').unlink(missing_ok=True)

        # Concatenate each produced module html file into one big file
        with open(output_file, "w") as fo:
            for html_file in out_modules_dir.glob('module_*.html'):
                with open(html_file,'r') as fi:
                    fo.write(fi.read())
                #Path(html_file).unlink(missing_ok=True)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file):
        """
        Convert a predicted pathway into the universal format
        @param raw_pathway_file: pathway file produced by an algorithm's run function
        @param standardized_pathway_file: the same pathway written in the universal format
        """
        edges = pd.DataFrame()

        with open(raw_pathway_file, 'r') as file:
            for line in file:
                if line.strip().startswith("let data = ["):
                    line2 = line.replace('let data = ', '')
                    line3 = line2.replace(';', '')

                    data = json.loads(line3)

                    entries = []
                    for entry in data:
                        tmp = entry['data']
                        entries.append(tmp)

                    df = pd.DataFrame(entries)
                    newdf = df.loc[:, ['source', 'target']].dropna()

                    edges = pd.concat([edges, newdf], axis=0)

        # DOMINO produces empty output files in some settings such as when it is run with small input files
        # and generates a ValueError
        if len(edges) > 0:
            edges['rank'] = 1  # Adds in a rank column of 1s because the edges are not ranked

            # Remove the prefix
            edges['source'] = edges['source'].apply(post_domino_id_transform)
            edges['target'] = edges['target'].apply(post_domino_id_transform)

        edges.to_csv(standardized_pathway_file, sep='\t', header=False, index=False)


def pre_domino_id_transform(node_id):
    """
    DOMINO algorithm requires module edges have 'ENSG0' string.
    Prepend each node id with ID_PREFIX
    @param node_id: the node id to transformed
    """
    return ID_PREFIX + node_id


def post_domino_id_transform(node_id):
    """
    Remove prefix
    @param node_id: the node id to transformed
    """
    node_id = node_id[len(ID_PREFIX):]
    return node_id
