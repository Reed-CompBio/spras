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

    def undirected_to_directed(self):
        df = pd.read_csv(IN_DIR+ 'test-network.csv', sep='\t')
        df = convert_undirected_to_directed(df)
        expected_df = pd.read_csv(EXPECTED_DIR+ 'u_to_d.csv', sep='\t')
        assert df.equals(expected_df)

    def directed_to_undirected(self):
        df = pd.read_csv(IN_DIR+ 'test-network.csv', sep='\t')
        df = convert_directed_to_undirected(df)
        expected_df = pd.read_csv(EXPECTED_DIR+'d_to_u.csv', sep='\t')
        assert df.equals(expected_df)

    def add_const(self):
        df = pd.read_csv(IN_DIR+ 'test-network.csv', sep='\t')
        df = add_constant(df, "const", "-")
        expected_df = pd.read_csv(EXPECTED_DIR+"add_const.csv", sep='\t')
        assert df.equals(expected_df)

    def add_directionality_const(self):
        df = pd.read_csv(IN_DIR+ 'test-network.csv', sep='\t')
        df = add_directionality_constant(df, "direct", "pd", "pp")
        expected_df = pd.read_csv(EXPECTED_DIR+"add_directionality_const.csv", sep='\t')
        assert df.equals(expected_df)

    def readd_col_mixed(self):
        assert True

    def readd_col_undir(self):
        assert True

    def readd_col_dir(self):
        assert True
