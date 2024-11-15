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

    def test_node_ensemble(self):
        ensemble_file = INPUT_DIR + 'ensemble-network.tsv'
        edge_freq = Evaluation.edge_frequency_node_ensemble(ensemble_file)
        edge_freq.to_csv(OUT_DIR + 'node-ensemble.csv', sep="\t", index=False)
        assert filecmp.cmp(OUT_DIR + 'node-ensemble.csv', EXPECT_DIR + 'expected-node-ensemble.csv', shallow=False)

    def test_precision_recal_curve_ensemble_nodes(self):
        out_path = Path(OUT_DIR+"test-precision-recall-curve-ensemble-nodes.png")
        out_path.unlink(missing_ok=True)
        ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble.csv', sep="\t", header=0)
        Evaluation.precision_recall_curve_node_ensemble(ensemble_file, NODE_TABLE, out_path)
        assert out_path.exists()

    def test_precision_recal_curve_ensemble_nodes_empty(self):
        out_path = Path(OUT_DIR+"test-precision-recall-curve-ensemble-nodes-empty.png")
        out_path.unlink(missing_ok=True)
        ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble-empty.csv', sep="\t", header=0)
        Evaluation.precision_recall_curve_node_ensemble(ensemble_file, NODE_TABLE, out_path)
        assert out_path.exists()

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


    def  test_precision_recall_pca_chosen_pathway(self):
        file_paths = [INPUT_DIR + "data-test-params-123/pathway.txt", INPUT_DIR + "data-test-params-456/pathway.txt",  INPUT_DIR + "data-test-params-789/pathway.txt",  INPUT_DIR + "data-test-params-empty/pathway.txt"]
        algorithms = ["test"]
        output_file = OUT_DIR +"test-precision-recall-per-pathway-pca-chosen.txt"
        output_png = OUT_DIR + "test-precision-recall-per-pathway-pca-chosen.png"

        dataframe = ml.summarize_networks(file_paths)
        ml.pca(dataframe, OUT_DIR + 'pca.png', OUT_DIR + 'pca-variance.txt', OUT_DIR + 'pca-coordinates.tsv')

        pathway = Evaluation.pca_chosen_pathway(OUT_DIR + 'pca-coordinates.tsv', INPUT_DIR)
        print(pathway)
        Evaluation.precision_and_recall(pathway, NODE_TABLE, algorithms, output_file, output_png)
        assert filecmp.cmp(output_file, EXPECT_DIR + 'expected-precision-recall-per-pathway-pca-chosen.txt', shallow=False)
