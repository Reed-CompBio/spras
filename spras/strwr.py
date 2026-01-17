from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict

from spras.config.container_schema import ProcessedContainerSettings
from spras.containers import prepare_volume, run_container_and_log
from spras.dataset import Dataset
from spras.interactome import (
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
)
from spras.prm import PRM
from spras.util import add_rank_column, duplicate_edges, raw_pathway_df

__all__ = ['ST_RWR', 'ST_RWRParams']

class ST_RWRParams(BaseModel):
    threshold: int
    "The number of nodes to return"

    alpha: Optional[float] = None
    "The chance of a restart during the random walk"

    model_config = ConfigDict(extra='forbid', use_attribute_docstrings=True)

# Note: This class is almost identical to the rwr.py file.
class ST_RWR(PRM[ST_RWRParams]):
    required_inputs = ['network','sources','targets']
    dois = []

    @staticmethod
    def generate_inputs(data, filename_map):
        """
        Access fields from the dataset and write the required input files
        @param data: dataset
        @param filename_map: a dict mapping file types in the required_inputs to the filename for that type. Associated files will be written with:
        - sources: list of sources
        - targets: list of targets
        - network: list of edges
        """
        ST_RWR.validate_required_inputs(filename_map)

        # Get separate source and target nodes for source and target files
        for node_type, nodes in data.get_node_columns_separate(["sources", "targets"]).items():
            nodes.to_csv(filename_map[node_type],sep='\t',index=False,columns=['NODEID'],header=False)

        # Get edge data for network file
        edges = data.get_interactome()
        edges = convert_undirected_to_directed(edges)

        edges.to_csv(filename_map['network'],sep='|',index=False,columns=['Interactor1', 'Interactor2', 'Weight'],header=False)

    @staticmethod
    def run(inputs, output_file, args, container_settings=None):
        if not container_settings: container_settings = ProcessedContainerSettings()
        ST_RWR.validate_required_run_args(inputs)

        with Path(inputs["network"]).open() as network_f:
            for line in network_f:
                line = line.strip()
                endpoints = line.split("|")
                if len(endpoints) != 3:
                    raise ValueError(f"Edge {line} does not contain 2 nodes and 1 weight separated by '|'")

        work_dir = '/spras'

        # Each volume is a tuple (src, dest)
        volumes = list()

        bind_path, source_file = prepare_volume(inputs["sources"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, target_file = prepare_volume(inputs["targets"], work_dir, container_settings)
        volumes.append(bind_path)

        bind_path, network_file = prepare_volume(inputs["network"], work_dir, container_settings)
        volumes.append(bind_path)

        # ST_RWR does not provide an argument to set the output directory
        # Use its --output argument to set the output file prefix to specify an absolute path and prefix
        out_dir = Path(output_file).parent
        # ST_RWR requires that the output directory exist
        out_dir.mkdir(parents=True, exist_ok=True)
        bind_path, mapped_out_dir = prepare_volume(str(out_dir), work_dir, container_settings)
        volumes.append(bind_path)
        mapped_out_prefix = mapped_out_dir + "/output.txt"
        command = ['python',
                   '/ST_RWR/ST_RWR.py',
                   '--network', network_file,
                   '--sources', source_file,
                   '--targets', target_file,
                   '--output', mapped_out_prefix]

        # Add alpha as an optional argument
        if args.alpha is not None:
            command.extend(['--alpha', str(args.alpha)])

        container_suffix = 'st-rwr:v1'
        run_container_and_log(
            "Source-Target RandomWalk with Restart",
            container_suffix,
            command,
            volumes,
            work_dir,
            out_dir,
            container_settings)

        # Rename the primary output file to match the desired output filename
        output_edges = Path(out_dir, 'output.txt')
        output_edges.rename(output_file)

    @staticmethod
    def parse_output(raw_pathway_file, standardized_pathway_file, params):
        df = raw_pathway_df(raw_pathway_file, sep='\t',header=0)
        if not df.empty:
            df.columns = ['node', 'score']
            if 'threshold' not in params:
                raise ValueError("threshold is a required parameter.")
            threshold = params['threshold']
            df = df.drop_duplicates(subset=['node'])
            df = df.sort_values(by=['score'], ascending=False)
            df = df.head(int(threshold))
            raw_dataset = Dataset.from_file(params.get('dataset'))
            interactome = raw_dataset.get_interactome().get(['Interactor1','Interactor2'])
            interactome = interactome[interactome['Interactor1'].isin(df['node'])
                                      & interactome['Interactor2'].isin(df['node'])]
            interactome = add_rank_column(interactome)
            interactome = reinsert_direction_col_directed(interactome)
            interactome.columns = ['Node1', 'Node2', 'Rank', "Direction"]
            interactome, has_duplicates = duplicate_edges(interactome)
            if has_duplicates:
                print(f"Duplicate edges were removed from {raw_pathway_file}")
            df = interactome
        df.to_csv(standardized_pathway_file, header = True, index=False, sep='\t')
