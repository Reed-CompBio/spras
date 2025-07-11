# This is a brief alternative to pyvis,
# which doesn't support mixed graphs.
import pandas as pd
from pathlib import Path


def visualize(network: pd.DataFrame, output: str):
    current_id = 0
    node_ids: dict[str, int] = dict()

    nodes_repr: list[str] = list()
    edges_repr: list[str] = list()
    
    for _index, row in network.iterrows():
        source_node = row["Node1"]
        target_node = row["Node2"]
        direction = row["Direction"]

        if source_node not in node_ids:
            node_ids[source_node] = current_id
            nodes_repr.append(f"{{id: {current_id}, label: '{source_node}'}}")
            current_id += 1

        if target_node not in node_ids:
            node_ids[target_node] = current_id
            nodes_repr.append(f"{{id: {current_id}, label: '{target_node}'}}")
            current_id += 1
        
        edges_repr.append(f"{{from: {node_ids[source_node]}, to: {node_ids[target_node]}}},")
