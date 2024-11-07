import filecmp
from pathlib import Path

import pandas as pd
import pytest

from spras.evaluation import Evaluation

INPUT_DIR = 'test/evaluate/input/'
OUT_DIR = 'test/evaluate/output/'
EXPECT_DIR = 'test/evaluate/expected/'


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
       
    def test_PRC_node_ensemble(self):
        None
        
    def test_precision_and_recall(self):
        None
    
    def test_pca_chosen_pathway(self):
        None
    
