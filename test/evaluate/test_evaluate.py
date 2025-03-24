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

    def test_precision_recall_per_pathway(self):
        file_paths = [INPUT_DIR + "data-test-params-123/pathway.txt", INPUT_DIR + "data-test-params-456/pathway.txt",  INPUT_DIR + "data-test-params-789/pathway.txt",  INPUT_DIR + "data-test-params-empty/pathway.txt"]
        algorithms = ["test"]
        output_file = OUT_DIR + "test-precision-recall-per-pathway.txt"
        output_png = OUT_DIR + "test-precision-recall-per-pathway.png"

        Evaluation.precision_and_recall(file_paths, NODE_TABLE, algorithms, output_file, output_png)
        assert filecmp.cmp(output_file, EXPECT_DIR + 'expected-precision-recall-per-pathway.txt', shallow=False)

    def test_precision_recall_per_pathway_empty(self):

        file_paths = [INPUT_DIR + "data-test-params-empty/pathway.txt"]
        algorithms = ["test"]
        output_file = OUT_DIR +"test-precision-recall-per-pathway-empty.txt"
        output_png = OUT_DIR + "test-precision-recall-per-pathway-empty.png"

        Evaluation.precision_and_recall(file_paths, NODE_TABLE, algorithms, output_file, output_png)
        assert filecmp.cmp(output_file, EXPECT_DIR + 'expected-precision-recall-per-pathway-empty.txt', shallow=False)
