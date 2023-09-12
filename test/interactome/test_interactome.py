from pathlib import Path

import pandas as pd

from src.interactome import (
    add_constant,
    add_directionality_constant,
    convert_directed_to_undirected,
    convert_undirected_to_directed,
    readd_direction_col_directed,
    readd_direction_col_mixed,
    readd_direction_col_undirected,
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
        columns = ['Interactor1','Interactor2','Weight','Direction']
        df = pd.read_csv(IN_DIR+ '/test-network.csv', sep='\t', header=None, names=columns)
        df = convert_undirected_to_directed(df)
        df.to_csv(OUT_DIR+"/output_u_to_d.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+ '/convert_u_to_d.csv', sep='\t', header=None, names=columns)
        assert df.equals(expected_df)

    def test_directed_to_undirected(self):
        columns = ['Interactor1','Interactor2','Weight','Direction']
        df = pd.read_csv(IN_DIR+ '/test-network.csv', sep='\t', header=None, names=columns)
        df = convert_directed_to_undirected(df)
        df.to_csv(OUT_DIR+"/output_d_to_u.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+'/convert_d_to_u.csv', sep='\t', header=None, names=columns)
        assert df.equals(expected_df)

    def test_add_const(self):
        columns = ['Interactor1','Interactor2','Weight','Direction']
        expected_columns = ['Interactor1','Interactor2','Weight','Direction', 'Const']
        df = pd.read_csv(IN_DIR+ '/test-network.csv', sep='\t', header=None, names=columns)
        df = add_constant(df, "Const", "-")
        df.to_csv(OUT_DIR+"/output_add_const.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+"/add_const.csv", sep='\t', header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_add_directionality_const(self):
        columns = ['Interactor1','Interactor2','Weight','Direction']
        expected_columns = ['Interactor1','Interactor2','Weight','Direction', 'Direct_Const']
        df = pd.read_csv(IN_DIR+ '/test-network.csv', sep='\t', header=None, names=columns)
        df = add_directionality_constant(df, "Direct_Const", "pd", "pp")
        df.to_csv(OUT_DIR+"/output_add_directionality_const.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+"/add_directionality_const.csv", sep='\t',  header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_readd_col_mixed(self):
        columns = ['Interactor1','Direct_Const','Interactor2','Weight']
        expected_columns = ['Interactor1','Direct_Const','Interactor2','Weight', 'Direction']
        df = pd.read_csv(IN_DIR+ '/test-readd-network.csv', sep='\t', header=None, names=columns)
        df = readd_direction_col_mixed(df, "Direct_Const", "pd", "pp")
        df.to_csv(OUT_DIR+"/output_readd_directiona_col_mixed.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+"/readd_mixed.csv", sep = '\t',header=None, names=expected_columns )
        assert df.equals(expected_df)

    def test_readd_col_undir(self):
        columns = ['Interactor1','Direct_Const','Interactor2','Weight']
        expected_columns = ['Interactor1','Direct_Const','Interactor2','Weight', 'Direction']
        df = pd.read_csv(IN_DIR+ '/test-readd-network.csv', sep='\t', header=None, names=columns)
        df = readd_direction_col_undirected(df)
        df.to_csv(OUT_DIR+"/output_readd_directiona_col_undir.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+"/readd_undir.csv", sep = '\t', header=None, names=expected_columns)
        assert df.equals(expected_df)

    def test_readd_col_dir(self):
        columns = ['Interactor1','Direct_Const','Interactor2','Weight']
        expected_columns = ['Interactor1','Direct_Const','Interactor2','Weight', 'Direction']
        df = pd.read_csv(IN_DIR+ '/test-readd-network.csv', sep='\t', header=None, names=columns)
        df = readd_direction_col_directed(df)
        df.to_csv(OUT_DIR+"/output_readd_directiona_col_dir.csv", sep='\t', index=False, header=False)
        expected_df = pd.read_csv(EXPECTED_DIR+"/readd_dir.csv", sep = '\t', header=None, names=expected_columns)
        assert df.equals(expected_df)
