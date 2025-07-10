import filecmp
from pathlib import Path

import pandas as pd
import pytest

import spras.analysis.ml as ml
from spras.evaluation import Evaluation

INPUT_DIR = 'test/evaluate/input/'
OUT_DIR = 'test/evaluate/output/'
EXPECT_DIR = 'test/evaluate/expected/'
GS_NODE_TABLE = pd.read_csv(INPUT_DIR + "node_table.csv", header=0)
class TestEvaluate:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_precision_recall_pca_chosen_pathway(self):
        # TODO: figure out why the pathawys chosen are different for github actions vs locally
        output_file = OUT_DIR +"test-pr-per-pathway-pca-chosen.txt"
        output_png = Path(OUT_DIR + "test-pr-per-pathway-pca-chosen.png")
        output_png.unlink(missing_ok=True)
        output_coordinates = Path(OUT_DIR + 'pca-coordinates.tsv')
        output_coordinates.unlink(missing_ok=True)

        file_paths = [INPUT_DIR + "data-test-params-123/pathway.txt", INPUT_DIR + "data-test-params-456/pathway.txt",  INPUT_DIR + "data-test-params-789/pathway.txt",  INPUT_DIR + "data-test-params-empty/pathway.txt"]
        algorithms = ["test"]

        dataframe = ml.summarize_networks(file_paths)
        ml.pca(dataframe, OUT_DIR + 'pca.png', OUT_DIR + 'pca-variance.txt', output_coordinates, OUT_DIR + 'pca-kde.txt', kernel_density=True, remove_empty_pathways=True)

        pathway = Evaluation.pca_chosen_pathway([output_coordinates], INPUT_DIR)
        Evaluation.precision_and_recall(pathway, GS_NODE_TABLE, algorithms, output_file, output_png)
        assert filecmp.cmp(output_file, EXPECT_DIR + 'expected-pr-per-pathway-pca-chosen.txt', shallow=False)
        assert output_png.exists()

# TODO test cases
# every coordinate/output is stacked on each other (no variance/kde)
# the pathways are colinear
# no unique points
# tie breaker situation