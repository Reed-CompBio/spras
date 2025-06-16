from pathlib import Path

from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import convert_directed_to_undirected
from spras.prm import PRM

__all__ = ['CapDSD']

class CapDSD(PRM):
    required_inputs = ['ppi', 'ppip.ppip']

    @staticmethod
    def generate_inputs(data: Dataset, filename_map: dict[str, str]):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        """
        for input_type in CapDSD.required_inputs:
            if input_type not in filename_map:
                raise ValueError(f"{input_type} filename is missing")

        # create the ppi
        ppi = data.get_interactome()
        ppi = convert_directed_to_undirected(ppi)
        ppi.to_csv(filename_map['ppi'], sep='\t', index=False, columns=["Interactor1", "Interactor2", "Weight"],
                   header=False)

        # then, we want to 'guide' the ppi with a .ppip file, which is a secondary,
        # trusted interactome: we use the directed edges from the interactome as our
        # trusted edges.
        ppip = data.get_interactome()
        ppip = ppip[ppip["Direction"] == "D"]
        ppip.to_csv(filename_map['ppip.ppip'], sep='\t', index=False, columns=["Interactor1", "Interactor2"], header=False)

    @staticmethod
    def run(ppi=None, ppip=None, output_file=None, container_framework="docker"):
        """
        Run BTB with Docker
        @param ppi:  input interactome file containing only undirected edges (required)
        @param ppip:  input interactome file containing only directed edges (required)
        @param output_file: path to the output matrix (required)
        @param container_framework: specify a container framework
        """
        if not ppi or not ppip or not output_file:
            raise ValueError("Required capDSD arguments are missing")

        work_dir = '/capDSD'

        volumes = list()

        bind_path, ppi_file = prepare_volume(ppi, work_dir)
        volumes.append(bind_path)

        bind_path, ppip_file = prepare_volume(ppip, work_dir)
        volumes.append(bind_path)

        # Create a prefix for the output filename and ensure the directory exists
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + '/output'

        container_suffix = "capdsd"

        # Since the volumes are binded under different folders, we can safely
        # use the ppip_file's parent.
        command = ['python',
                   '/capDSD/DSD.py',
                   '-pathmode', '1',
                   '-p', str(Path(ppip_file).parent),
                   ppi_file, mapped_out_prefix]


        run_container_and_log('capDSD',
                              container_framework,
                              container_suffix,
                              command,
                              volumes,
                              work_dir)

        output_matrix = Path(out_dir) / 'output.dsd'
        output_matrix.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file: str, standardized_pathway_file: str):
        pass
