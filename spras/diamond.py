from pathlib import Path

from pydantic import BaseModel, ConfigDict

from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_directed_to_undirected,
    reinsert_direction_col_undirected,
)
from spras.prm import PRM
from spras.util import duplicate_edges, raw_pathway_df, shrink_rank_column

__all__ = ['DIAMOnD', 'DIAMOnDParams']

class DIAMOnDParams(BaseModel):
    n: int
    """The desired number of DIAMOnD genes to add."""

    alpha: int = 1
    """Weight of the seeds"""

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

class DIAMOnD(PRM[DIAMOnDParams]):
    """
    DIAMOnD is a disease module detection algorithm,
    which has been modified here, using actives as seeds, to act as a pathway reconstruction algorithm.
    It does not account for node scores, and takes in undirected graphs as input.
    """
    required_inputs = ['seeds', 'network']
    dois = ["10.1371/journal.pcbi.1004120"]

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type
        - seeds: newline-delimited seeds file
        - network: no-header two-column input directed network file
        """
        for input_type in DIAMOnD.required_inputs:
            if input_type not in filename_map:
                raise ValueError("{input_type} filename is missing")

        # Create seeds file - we set the seeds as the actives
        actives = data.get_node_columns(["active"])
        if actives is None:
            return False
        seeds_df = actives[(actives["active"] == True)]
        seeds_df = seeds_df.sort_values(by=[Dataset.NODE_ID], ascending=True, ignore_index=True)
        seeds_df.to_csv(filename_map['seeds'], index=False, columns=[Dataset.NODE_ID], header=None)

        # Create network file
        edges_df = data.get_interactome()
        edges_df = convert_directed_to_undirected(edges_df)
        edges_df.to_csv(filename_map["network"], columns=["Interactor1", "Interactor2"], index=False, header=None, sep=',')

    @staticmethod
    def run(inputs, output_file, args, container_settings=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        DIAMOnD.validate_required_run_args(inputs)

        work_dir = '/diamond'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, seeds_file = prepare_volume(inputs["seeds"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(inputs["network"], work_dir, container_settings)
        volumes.append(bind_path)

        # Create the parent directories for the output file if needed
        out_dir = Path(output_file).parent
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_file = prepare_volume(output_file, work_dir, container_settings)
        volumes.append(bind_path)

        command = ['python',
                   '/DIAMOnD.py',
                   network_file,
                   seeds_file,
                   str(args.n),
                   str(args.alpha),
                   mapped_out_file]

        container_suffix = "diamond:latest"
        run_container_and_log('DIAMOND',
                              container_suffix,
                              command,
                              volumes,
                              work_dir,
                              out_dir,
                              container_settings)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        df = raw_pathway_df(raw_pathway_file, sep='\t', header=0)
        if not df.empty:
            # preprocessing - drop [useful] p_hyper information, and rename columns to Rank and Node
            df = df.drop(columns=["p_hyper"])
            df.columns = ["Rank", "Node"]

            original_dataset: Dataset = params['dataset']
            interactome = original_dataset.get_interactome().get(['Interactor1','Interactor2'])
            interactome = interactome[interactome['Interactor1'].isin(df['Node'])
                                      & interactome['Interactor2'].isin(df['Node'])]

            interactome = interactome.merge(df.rename(columns={"Rank": "Rank1", "Node": "Interactor1"}),
                                            how='inner', on='Interactor1')
            interactome = interactome.merge(df.rename(columns={"Rank": "Rank2", "Node": "Interactor2"}),
                                            how='inner', on='Interactor2')
            interactome["Rank"] = interactome["Rank1"] + interactome["Rank2"]
            interactome = interactome.drop(columns=["Rank1", "Rank2"])

            interactome = shrink_rank_column(interactome)

            interactome = reinsert_direction_col_undirected(interactome)
            interactome.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            interactome, has_duplicates = duplicate_edges(interactome)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
            df = interactome
        df.to_csv(standardized_pathway_file, header=True, index=False, sep='\t')
