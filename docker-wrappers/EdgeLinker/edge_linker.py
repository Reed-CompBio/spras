import argparse
from itertools import chain, islice
from pathlib import Path

import networkx as nx

# The tiny and miny game actions from combinatorial game theory.
# These two symbols are meant to be widely unused.
SUPER_SOURCE = "⧾"
SUPER_TARGET = "⧿"

# https://stackoverflow.com/a/6822773/7589775
def window(seq, n=2):
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def score_path(G: nx.DiGraph, path: list[str]) -> int:
    score = 0
    for i in range(0, len(path) - 1):
        source = path[i]
        target = path[i + 1]
        score = score + float(G.get_edge_data(source, target)['weight'])
    return score

def edge_linker(network_file: Path, sources_file: Path, targets_file: Path) -> tuple[nx.DiGraph, list[str]]:
    if not network_file.exists():
        raise OSError(f"Network file {str(network_file)} does not exist.")
    if not sources_file.exists():
        raise OSError(f"Sources file {str(sources_file)} does not exist.")
    if not targets_file.exists():
        raise OSError(f"Targets file {str(targets_file)} does not exist.")

    sources = filter(lambda source: source.strip(), sources_file.read_text().splitlines())
    targets = filter(lambda target: target.strip(), targets_file.read_text().splitlines())

    # Parse and store network file
    G = nx.DiGraph()
    with network_file.open() as network_reader:
        for line in network_reader:
            items = line.split('\t')
            if len(items) != 3:
                raise IndexError(f"Line {line} does not have 3 items!")
            [source, target, weight] = line.split('\t')
            G.add_edge(source, target, weight=weight)

    # Add super source/target. TODO: check if these nodes already exist
    G.add_node(SUPER_SOURCE)
    G.add_node(SUPER_TARGET)
    for source in sources:
        G.add_edge(SUPER_SOURCE, source, weight=1)
    for target in targets:
        G.add_edge(target, SUPER_TARGET, weight=1)

    shortest_paths: dict[str, list[str]] = nx.shortest_path(G, SUPER_SOURCE)
    # Instead of trying to deal with double-reversing the graph, we just use dijkstra's algorithm from every possible source to the super target.
    shortest_paths_reverse: dict[str, list[str]] = nx.shortest_path(G, None, SUPER_TARGET)

    joined_paths: list[list[str]] = []
    for middle, path in shortest_paths.items():
        end_path = shortest_paths_reverse[middle]
        path = path[:-1] + end_path
        joined_paths.append(path)

    return (G, sorted(joined_paths, key=lambda path: score_path(G, path)))

def path_subgraph(G: nx.DiGraph, paths: list[list[str]]):
    edges = map(lambda path: window(path, n=2), paths)
    # https://stackoverflow.com/a/953097/7589775
    edges = list(chain.from_iterable(edges))
    return G.edge_subgraph(edges)

def main():
    parser = argparse.ArgumentParser(
        description="EdgeLinker Pathway Reconstruction"
    )
    parser.add_argument("--network", type=Path, required=True, help="Path to the network file, tab-separated, directed graph, with source, target, and weight. No headers.")
    parser.add_argument("--sources", type=Path, required=True, help="Path to the sources, newline-separated.")
    parser.add_argument("--targets", type=Path, required=True, help="Path to the targets, newline-separated.")
    parser.add_argument("--output", type=Path, required=True, help="Path to the output file. Tab-separated, source and target per line.")
    parser.add_argument("-k", type=int, required=True, help="Amount of paths that EdgeLinker returns.")

    arguments = parser.parse_args()
    (G, paths) = edge_linker(arguments.network, arguments.sources, arguments.targets)

    # Avoid missing directory errors
    arguments.output.parent.mkdir(parents=True, exist_ok=True)

    print(f"Found {len(paths)} paths - the k value, {arguments.k}, prunes a path count of {len(paths) - len(paths[:arguments.k])}")

    sub_G = path_subgraph(G, paths[:arguments.k])
    with Path(arguments.output).open('+w', encoding="utf-8") as out_writer:
        for (source, target) in sub_G.edges():
            if source == SUPER_SOURCE or target == SUPER_TARGET:
                continue
            out_writer.write(f"{source}\t{target}\n")

if __name__ == '__main__':
    main()
