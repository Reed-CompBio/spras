import filecmp
from pathlib import Path

import pandas as pd
import pytest

import spras.analysis.ml as ml
from spras.evaluation import Evaluation

INPUT_DIR = 'test/evaluate/input/'
OUT_DIR = 'test/evaluate/output/'
EXPECT_DIR = 'test/evaluate/expected/'
NODE_TABLE = pd.read_csv(INPUT_DIR + "node_table.csv", header=0)
class TestEvaluate:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def  test_precision_recall_pca_chosen_pathway(self):
        file_paths = [INPUT_DIR + "data-test-params-123/pathway.txt", INPUT_DIR + "data-test-params-456/pathway.txt",  INPUT_DIR + "data-test-params-789/pathway.txt",  INPUT_DIR + "data-test-params-empty/pathway.txt"]
        algorithms = ["test"]
        output_file = OUT_DIR +"test-precision-recall-per-pathway-pca-chosen.txt"
        output_png = OUT_DIR + "test-precision-recall-per-pathway-pca-chosen.png"

        dataframe = ml.summarize_networks(file_paths)
        ml.pca(dataframe, OUT_DIR + 'pca.png', OUT_DIR + 'pca-variance.txt', OUT_DIR + 'pca-coordinates.tsv')

        pathway = Evaluation.pca_chosen_pathway(OUT_DIR + 'pca-coordinates.tsv', INPUT_DIR)
        Evaluation.precision_and_recall(pathway, NODE_TABLE, algorithms, output_file, output_png)
        assert filecmp.cmp(output_file, EXPECT_DIR + 'expected-precision-recall-per-pathway-pca-chosen.txt', shallow=False)
