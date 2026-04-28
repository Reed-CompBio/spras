from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_directed_to_undirected,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.secrets import gurobi
from spras.util import add_rank_column, duplicate_edges

__all__ = ['NetMix2']

class NetMix2Params(BaseModel):
    delta: Optional[float] = None
    """The similarity threshold (optional)."""
    num_edges: int = 175000
    """The number of edges in similarity threshold graph."""
    density: float = 0.05
    """The minimum edge density of the altered subnetwork."""

class NetMix2(PRM):
    required_inputs = ['network', 'scores']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: Dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in NetMix2.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        if data.contains_node_columns('prize'):
            node_df = data.get_node_columns(['prize'])
        else:
            raise ValueError("Node prizes are required for NetMix2.")
        node_df.to_csv(filename_map['scores'], index=False, columns=['prize', 'NODEID'], header=False, sep='\t')

        edges_df = data.get_interactome()
        edges_df = convert_directed_to_undirected(edges_df)
        edges_df.to_csv(filename_map['network'], index=False, sep='\t', columns=['Interactor1', 'Interactor2'], header=False)

    @staticmethod
    def run(inputs, output_file, args, container_settings=None):
        gurobi_path = gurobi()
        if not gurobi_path:
            raise RuntimeError("gurobi license path is not present.\n" + \
                               "Make sure to specify the path in secrets.gurobi in `config.yaml`.")

        work_dir = '/spras'

        volumes = list()

        bind_path, network_file = prepare_volume(inputs["network"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, scores_file = prepare_volume(inputs["scores"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, license_file = prepare_volume(inputs["gurobi_path"], work_dir, container_settings)
        volumes.append(bind_path)

        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)

        bind_path, mapped_out_dir = prepare_volume(out_dir, work_dir, container_settings)
        volumes.append(bind_path)

        command = ['python',
                   '/NetMix2/run_netmix2.py',
                   '-el',
                   network_file,
                   '-gs',
                   scores_file,
                   '-o', mapped_out_dir]

        # Add optional arguments
        if args.delta is not None:
            command.extend(['--delta', str(args.delta)])
        command.extend(['--num_edges', str(args.num_edges)])
        command.extend(['--density', str(args.density)])

        container_suffix = "netmix2"
        run_container_and_log('NetMix2',
                              container_suffix,
                              command,
                              volumes,
                              work_dir,
                              out_dir,
                              container_settings,
                              environment={'SPRAS': 'True',
                                           'GRB_LICENSE_FILE': license_file})

        # Rename the primary output file to match the desired output filename
        output_vertices = out_dir / 'netmix_subnetwork.tsv'
        output_vertices.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        with open(raw_pathway_file) as raw_pathway_file:
            vertices = [line.rstrip('\n') for line in raw_pathway_file if not str.isspace(line)]

        original_dataset = Dataset.from_file(params.get('dataset'))
        interactome = original_dataset.get_interactome().get(['Interactor1','Interactor2'])
        interactome = interactome[interactome['Interactor1'].isin(vertices)
                                    & interactome['Interactor2'].isin(vertices)]
        interactome = add_rank_column(interactome)
        interactome = reinsert_direction_col_undirected(interactome)
        interactome.columns = ['Node1', 'Node2', 'Rank', "Direction"]
        interactome, has_duplicates = duplicate_edges(interactome)
        if has_duplicates:
            print(f"Duplicate edges were removed from {raw_pathway_file}")
        interactome.to_csv(standardized_pathway_file, header = True, index=False, sep='\t')
