import urllib.parse
from pathlib import Path

import requests

from spras.runner import algorithms

DOI_BASE = "https://citation.doi.org/format?style=bibtex&lang=en-US&doi="

def format_request(doi: str) -> str:
    return DOI_BASE + urllib.parse.quote(doi)

def get_bibtex(doi: str) -> str:
    response = requests.get(format_request(doi))

    return response.text.strip()

def attribute_algorithms(all_file: str, alg_files: list[str]):
    """
    Attributes all algorithms specified by alg_files, aggregating them in
    all_file.
    """
    algorithm_name_files = [(Path(file).stem, file) for file in alg_files]

    algorithm_citations = [
        (file, [get_bibtex(doi) for doi in algorithms[name].dois]) for (name, file) in algorithm_name_files
    ]

    for alg_output, alg_citations in algorithm_citations:
        Path(alg_output).parent.mkdir(parents=True, exist_ok=True)
        with open(alg_output, '+w') as handle:
            for citation in alg_citations:
                handle.write(citation + '\n')

    Path(all_file).parent.mkdir(parents=True, exist_ok=True)
    with open(all_file, '+w') as handle:
        for _, alg_citations in algorithm_citations:
            for citation in alg_citations:
                handle.write(citation + '\n')
