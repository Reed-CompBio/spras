import filecmp
from pathlib import Path

import pandas as pd
import pytest

import spras.analysis.ml as ml
from spras.evaluation import Evaluation

INPUT_DIR = 'test/evaluate/input/'
OUT_DIR = 'test/evaluate/output/'
EXPECT_DIR = 'test/evaluate/expected/'
GS_NODE_TABLE = pd.read_csv(INPUT_DIR + "gs_node_table.csv", header=0)
class TestEvaluate:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_node_ensemble(self):
        ensemble_network = [INPUT_DIR + 'ensemble-network.tsv']
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(GS_NODE_TABLE, ensemble_network)
        node_ensemble_dict['ensemble'].to_csv(OUT_DIR + 'node-ensemble.csv', sep="\t", index=False)
        assert filecmp.cmp(OUT_DIR + 'node-ensemble.csv', EXPECT_DIR + 'expected-node-ensemble.csv', shallow=False)

    def test_empty_node_ensemble(self):
        empty_ensemble_network = [INPUT_DIR + 'empty-ensemble-network.tsv']
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(GS_NODE_TABLE, empty_ensemble_network)
        node_ensemble_dict['empty'].to_csv(OUT_DIR + 'empty-node-ensemble.csv', sep="\t", index=False)
        assert filecmp.cmp(OUT_DIR + 'empty-node-ensemble.csv', EXPECT_DIR + 'expected-node-ensemble-empty.csv', shallow=False)

    def test_multiple_node_ensemble(self):
        ensemble_networks = [INPUT_DIR + 'ensemble-network.tsv', INPUT_DIR + 'empty-ensemble-network.tsv']
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(GS_NODE_TABLE, ensemble_networks)
        node_ensemble_dict['ensemble'].to_csv(OUT_DIR + 'node-ensemble.csv', sep="\t", index=False)
        assert filecmp.cmp(OUT_DIR + 'node-ensemble.csv', EXPECT_DIR + 'expected-node-ensemble.csv', shallow=False)
        node_ensemble_dict['empty'].to_csv(OUT_DIR + 'empty-node-ensemble.csv', sep="\t", index=False)
        assert filecmp.cmp(OUT_DIR + 'empty-node-ensemble.csv', EXPECT_DIR + 'expected-node-ensemble-empty.csv', shallow=False)

    def test_precision_recall_curve_ensemble_nodes(self):
        out_path = Path(OUT_DIR+"test-precision-recall-curve-ensemble-nodes.png")
        out_path.unlink(missing_ok=True)
        ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble.csv', sep="\t", header=0)
        node_ensembles_dict = {'ensemble': ensemble_file}
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, GS_NODE_TABLE, out_path)
        assert out_path.exists()

    def test_precision_recall_curve_ensemble_nodes_empty(self):
        out_path = Path(OUT_DIR+"test-precision-recall-curve-ensemble-nodes-empty.png")
        out_path.unlink(missing_ok=True)
        empty_ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble-empty.csv', sep="\t", header=0)
        node_ensembles_dict = {'ensemble': empty_ensemble_file}
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, GS_NODE_TABLE, out_path)
        assert out_path.exists()

    def test_precision_recall_curve_multiple_ensemble_nodes(self):
        out_path = Path(OUT_DIR+"test-precision-recall-curve-multiple-ensemble-nodes.png")
        out_path.unlink(missing_ok=True)
        ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble.csv', sep="\t", header=0)
        empty_ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble-empty.csv', sep="\t", header=0)
        node_ensembles_dict = {'ensemble1': ensemble_file, 'ensemble2': ensemble_file, 'ensemble3': empty_ensemble_file}
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, GS_NODE_TABLE, out_path)
        assert out_path.exists()
