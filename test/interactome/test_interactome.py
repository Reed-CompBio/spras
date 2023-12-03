from pathlib import Path

import pandas as pd
import pytest

from spras.dataset import Dataset
from spras.interactome import (
    add_constant,
    add_directionality_constant,
    convert_directed_to_undirected,
    convert_undirected_to_directed,
    reinsert_direction_col_directed,
    reinsert_direction_col_mixed,
    reinsert_direction_col_undirected,
)

IN_DIR = "test/interactome/input"
OUT_DIR = "test/interactome/output/"
EXPECTED_DIR = "test/interactome/expected"


class TestInteractome:
    @classmethod
    def setup_class(cls):
        """
        Create the expected output directory
        """
        Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

    def test_undirected_to_directed(self):
        columns = ['Interactor1', 'Interactor2', 'Weight', 'Direction']
        df = pd.read_csv(IN_DIR + '/test-network.txt', sep='\t', header=None, names=columns)
        df = convert_undirected_to_directed(df)
        df.to_csv(OUT_DIR + "/output_u_to_d.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + '/convert_u_to_d.txt', sep='\t', header=None, names=columns)
        assert df.equals(expected_df)

    def test_directed_to_undirected(self):
        columns = ['Interactor1', 'Interactor2', 'Weight', 'Direction']
        df = pd.read_csv(IN_DIR + '/test-network.txt', sep='\t', header=None, names=columns)
        df = convert_directed_to_undirected(df)
        df.to_csv(OUT_DIR + "/output_d_to_u.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + '/convert_d_to_u.txt', sep='\t', header=None, names=columns)
        assert df.equals(expected_df)

    def test_add_const(self):
        columns = ['Interactor1', 'Interactor2', 'Weight', 'Direction']
        expected_columns = ['Interactor1', 'Interactor2', 'Weight', 'Direction', 'Const']
        df = pd.read_csv(IN_DIR + '/test-network.txt', sep='\t', header=None, names=columns)
        df = add_constant(df, "Const", "-")
        df.to_csv(OUT_DIR + "/output_add_const.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + "/add_const.txt", sep='\t', header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_add_directionality_const(self):
        columns = ['Interactor1', 'Interactor2', 'Weight', 'Direction']
        expected_columns = ['Interactor1', 'Interactor2', 'Weight', 'Direction', 'Direct_Const']
        df = pd.read_csv(IN_DIR + '/test-network.txt', sep='\t', header=None, names=columns)
        df = add_directionality_constant(df, "Direct_Const", "pd", "pp")
        df.to_csv(OUT_DIR + "/output_add_directionality_const.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + "/add_directionality_const.txt", sep='\t', header=None,
                                  names=expected_columns)
        assert df.equals(expected_df)

    def test_reinsert_col_mixed(self):
        columns = ['Interactor1', 'Direct_Const', 'Interactor2', 'Weight']
        expected_columns = ['Interactor1', 'Direct_Const', 'Interactor2', 'Weight', 'Direction']
        df = pd.read_csv(IN_DIR + '/test-reinsert-network.txt', sep='\t', header=None, names=columns)
        df = reinsert_direction_col_mixed(df, "Direct_Const", "pd", "pp")
        df.to_csv(OUT_DIR + "/output_reinsert_direction_col_mixed.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + "/reinsert_mixed.txt", sep='\t', header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_reinsert_col_undir(self):
        columns = ['Interactor1', 'Direct_Const', 'Interactor2', 'Weight']
        expected_columns = ['Interactor1', 'Direct_Const', 'Interactor2', 'Weight', 'Direction']
        df = pd.read_csv(IN_DIR + '/test-reinsert-network.txt', sep='\t', header=None, names=columns)
        df = reinsert_direction_col_undirected(df)
        df.to_csv(OUT_DIR + "/output_reinsert_direction_col_undir.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + "/reinsert_undir.txt", sep='\t', header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_reinsert_col_dir(self):
        columns = ['Interactor1', 'Direct_Const', 'Interactor2', 'Weight']
        expected_columns = ['Interactor1', 'Direct_Const', 'Interactor2', 'Weight', 'Direction']
        df = pd.read_csv(IN_DIR + '/test-reinsert-network.txt', sep='\t', header=None, names=columns)
        df = reinsert_direction_col_directed(df)
        df.to_csv(OUT_DIR + "/output_reinsert_direction_col_dir.txt", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR + "/reinsert_dir.txt", sep='\t', header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_invalid_value(self):
        """
        Test error is thrown when fourth column of edge file has an invalid value (not D or U)
        """
        with pytest.raises(ValueError):
            dataset_info = {'label': 'test',
                            'edge_files': ['test-network-invalid-value.txt'],
                            'node_files': None,  # Will raise error before loading node table
                            'data_dir': IN_DIR
                            }
            Dataset(dataset_info)

    def test_missing_value(self):
        """
        Test error is thrown when fourth column of edge file is missing
        """
        with pytest.raises(ValueError):
            dataset_info = {'label': 'test',
                            'edge_files': ['test-network-missing-value.txt'],
                            'node_files': None,  # Will raise error before loading node table
                            'data_dir': IN_DIR
                            }
            Dataset(dataset_info)
