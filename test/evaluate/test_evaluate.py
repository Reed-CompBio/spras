import filecmp
import pickle
from pathlib import Path

import pandas as pd

import spras.analysis.ml as ml
from spras.dataset import Dataset
from spras.evaluation import Evaluation

INPUT_DIR = 'test/evaluate/input/'
OUT_DIR = 'test/evaluate/output/'
EXPECT_DIR = 'test/evaluate/expected/'
GS_NODE_TABLE = pd.read_csv(INPUT_DIR + 'gs_node_table.csv', header=0)
SUMMARY_FILE = INPUT_DIR + 'example_summary.txt'


class TestEvaluate:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory and pickled toy dataset file
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

        out_dataset = Path(OUT_DIR, 'data.pickle')
        out_dataset.unlink(missing_ok=True)

        dataset = Dataset({
            "label": 'toy',
            "edge_files": ["input-interactome.txt"],
            "node_files": ["input-nodes.txt"],
            "data_dir": INPUT_DIR,
            "other_files": []
        })

        with open(out_dataset, "wb") as f:
            pickle.dump(dataset, f)

    def test_precision_recall_pca_chosen_pathway(self):
        output_file = Path(OUT_DIR + "test-pr-per-pathway-pca-chosen.txt")
        output_file.unlink(missing_ok=True)
        output_png = Path(OUT_DIR + "test-pr-per-pathway-pca-chosen.png")
        output_png.unlink(missing_ok=True)
        output_coordinates = Path(OUT_DIR + "pca-coordinates.tsv")
        output_coordinates.unlink(missing_ok=True)

        file_paths = [INPUT_DIR + "data-test-params-123/pathway.txt", INPUT_DIR + "data-test-params-456/pathway.txt",
                      INPUT_DIR + "data-test-params-789/pathway.txt",  INPUT_DIR + "data-test-params-empty/pathway.txt"]
        algorithms = ["test"]

        dataframe = ml.summarize_networks(file_paths)
        ml.pca(dataframe, OUT_DIR + 'pca.png', OUT_DIR + 'pca-variance.txt', output_coordinates, kde=True, remove_empty_pathways=True)

        pathway = Evaluation.pca_chosen_pathway([output_coordinates], SUMMARY_FILE, INPUT_DIR)
        Evaluation.precision_and_recall(pathway, GS_NODE_TABLE, algorithms, str(output_file), str(output_png))

        chosen = pd.read_csv(output_file, sep="\t", header=0).round(8)
        expected = pd.read_csv(EXPECT_DIR + "expected-pr-per-pathway-pca-chosen.txt", sep="\t", header=0).round(8)
        # For windows support
        expected.insert(loc=0, column='Pathway', value=[str(Path("test", "evaluate", "input", "data-test-params-123", "pathway.txt"))])

        pd.set_option('display.max_colwidth', None)
        print()
        print(chosen)
        print(expected)
        assert chosen.equals(expected)
        assert output_png.exists()

    def test_precision_recall_pca_chosen_pathway_not_provided(self):
        output_file = OUT_DIR +"test-pr-per-pathway-pca-chosen-not-provided.txt"
        output_png = Path(OUT_DIR + "test-pr-per-pathway-pca-chosen-not-provided.png")
        output_png.unlink(missing_ok=True)

        algorithms = ["test"]
        Evaluation.precision_and_recall([], GS_NODE_TABLE, algorithms, str(output_file), str(output_png))

        chosen = pd.read_csv(output_file, sep="\t", header=0).round(8)
        expected = pd.read_csv(EXPECT_DIR + 'expected-pr-per-pathway-pca-chosen-not-provided.txt', sep="\t",  header=0).round(8)

        assert chosen.equals(expected)
        assert output_png.exists()

    def test_node_ensemble(self):
        out_path_file = Path(OUT_DIR + 'node-ensemble.csv')
        out_path_file.unlink(missing_ok=True)
        ensemble_network = [INPUT_DIR + 'ensemble-network.tsv']
        input_network = OUT_DIR + 'data.pickle'
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(GS_NODE_TABLE, ensemble_network, input_network)
        node_ensemble_dict['ensemble'].to_csv(out_path_file, sep='\t', index=False)
        assert filecmp.cmp(out_path_file, EXPECT_DIR + 'expected-node-ensemble.csv', shallow=False)

    def test_empty_node_ensemble(self):
        out_path_file = Path(OUT_DIR + 'empty-node-ensemble.csv')
        out_path_file.unlink(missing_ok=True)
        empty_ensemble_network = [INPUT_DIR + 'empty-ensemble-network.tsv']
        input_network = OUT_DIR + 'data.pickle'
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(GS_NODE_TABLE, empty_ensemble_network,
                                                                     input_network)
        node_ensemble_dict['empty'].to_csv(out_path_file, sep='\t', index=False)
        assert filecmp.cmp(out_path_file, EXPECT_DIR + 'expected-empty-node-ensemble.csv', shallow=False)

    def test_multiple_node_ensemble(self):
        out_path_file = Path(OUT_DIR + 'node-ensemble.csv')
        out_path_file.unlink(missing_ok=True)
        out_path_empty_file = Path(OUT_DIR + 'empty-node-ensemble.csv')
        out_path_empty_file.unlink(missing_ok=True)
        ensemble_networks = [INPUT_DIR + 'ensemble-network.tsv', INPUT_DIR + 'empty-ensemble-network.tsv']
        input_network = OUT_DIR + 'data.pickle'
        node_ensemble_dict = Evaluation.edge_frequency_node_ensemble(GS_NODE_TABLE, ensemble_networks, input_network)
        node_ensemble_dict['ensemble'].to_csv(out_path_file, sep='\t', index=False)
        assert filecmp.cmp(out_path_file, EXPECT_DIR + 'expected-node-ensemble.csv', shallow=False)
        node_ensemble_dict['empty'].to_csv(out_path_empty_file, sep='\t', index=False)
        assert filecmp.cmp(out_path_empty_file, EXPECT_DIR + 'expected-empty-node-ensemble.csv', shallow=False)

    def test_precision_recall_curve_ensemble_nodes(self):
        out_path_png = Path(OUT_DIR + "pr-curve-ensemble-nodes.png")
        out_path_png.unlink(missing_ok=True)
        out_path_file = Path(OUT_DIR + "pr-curve-ensemble-nodes.txt")
        out_path_file.unlink(missing_ok=True)
        ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble.csv', sep='\t', header=0)
        node_ensembles_dict = {'ensemble': ensemble_file}
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, GS_NODE_TABLE, str(out_path_png),
                                                        str(out_path_file))
        assert out_path_png.exists()
        assert filecmp.cmp(out_path_file, EXPECT_DIR + 'expected-pr-curve-ensemble-nodes.txt', shallow=False)

    def test_precision_recall_curve_ensemble_nodes_empty(self):
        out_path_png = Path(OUT_DIR + "pr-curve-ensemble-nodes-empty.png")
        out_path_png.unlink(missing_ok=True)
        out_path_file = Path(OUT_DIR + "pr-curve-ensemble-nodes-empty.txt")
        out_path_file.unlink(missing_ok=True)
        empty_ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble-empty.csv', sep='\t', header=0)
        node_ensembles_dict = {'ensemble': empty_ensemble_file}
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, GS_NODE_TABLE, str(out_path_png),
                                                        str(out_path_file))
        assert out_path_png.exists()
        assert filecmp.cmp(out_path_file, EXPECT_DIR + 'expected-pr-curve-ensemble-nodes-empty.txt', shallow=False)

    def test_precision_recall_curve_multiple_ensemble_nodes(self):
        out_path_png = Path(OUT_DIR + "pr-curve-multiple-ensemble-nodes.png")
        out_path_png.unlink(missing_ok=True)
        out_path_file = Path(OUT_DIR + "pr-curve-multiple-ensemble-nodes.txt")
        out_path_file.unlink(missing_ok=True)
        ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble.csv', sep='\t', header=0)
        empty_ensemble_file = pd.read_csv(INPUT_DIR + 'node-ensemble-empty.csv', sep='\t', header=0)
        node_ensembles_dict = {'ensemble1': ensemble_file, 'ensemble2': ensemble_file, 'ensemble3': empty_ensemble_file}
        Evaluation.precision_recall_curve_node_ensemble(node_ensembles_dict, GS_NODE_TABLE, str(out_path_png),
                                                        str(out_path_file))
        assert out_path_png.exists()
        assert filecmp.cmp(out_path_file, EXPECT_DIR + 'expected-pr-curve-multiple-ensemble-nodes.txt', shallow=False)
