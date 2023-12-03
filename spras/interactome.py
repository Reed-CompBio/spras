"""
Author: Neha Talluri
07/19/23

Methods for converting from the universal network input format and to the universal network output format
"""

import pandas as pd


def convert_undirected_to_directed(df: pd.DataFrame) -> pd.DataFrame:
    """
    turns a graph into a fully directed graph
    - turns every undirected edge into a pair of directed edges
    - with the pair of directed edges, we are not losing too much information because the relationship of the undirected
      edge is still preserved

    @param df: input network df of edges, weights, and directionality
    @return a dataframe with no undirected edges in Direction column
    """

    mask = df['Direction'] == 'U'
    new_df = df[mask].copy(deep=True)
    new_df['Interactor1'], new_df['Interactor2'] = new_df['Interactor2'], new_df['Interactor1']
    new_df['Direction'] = 'D'
    df.loc[mask, 'Direction'] = 'D'
    df = pd.concat([df, new_df], ignore_index=True)
    return df


def convert_directed_to_undirected(df: pd.DataFrame) -> pd.DataFrame:
    """
    turns a graph into a fully undirected graph
    - turns all the directed edges directly into undirected edges
    - we will lose any sense of directionality and the graph won't be inherently accurate, but the basic relationship
      between the two connected nodes will still remain intact.

    @param df: input network df of edges, weights, and directionality
    @return a dataframe with no directed edges in Direction column
    """

    df["Direction"] = "U"

    return df


def add_constant(df: pd.DataFrame, new_col_name: str, const) -> pd.DataFrame:
    """
    adds a new column at the end of the input dataframe with a constant value in all rows

    @param df: input network df of edges, weights, and directionality
    @param new_col_name: the name of the new column
    @param const: some type of constant needed in the df
    @return a df with a new constant added to every row
    """

    df.insert(df.shape[1], new_col_name, const)

    return df


def add_directionality_constant(df: pd.DataFrame,  col_name: str, dir_const, undir_const) -> pd.DataFrame:
    """
    deals with adding in directionality constants for mixed graphs that aren't using the universal input directly

    @param df: input network df of edges, weights, and directionality
    @param col_name: the name of the new column
    @param dir_const: the directed edge const
    @param undir_const: the undirected edge const
    @return a df converted to show directionality differently
    """

    df.insert(df.shape[1], col_name, "NA")

    mask = df['Direction'] == 'U'
    df.loc[mask, col_name] = undir_const

    mask = df['Direction'] == 'D'
    df.loc[mask, col_name] = dir_const

    if not df[col_name].isin([dir_const, undir_const]).all():
        raise ValueError(f"The column '{col_name}' contains values other than '{dir_const}' and '{undir_const}'")

    return df


def reinsert_direction_col_mixed(df: pd.DataFrame, existing_direction_column: str, dir_const: str, undir_const: str) -> pd.DataFrame:
    """
    adds back a 'Direction' column that puts a 'U' or 'D' at the end of provided dataframe
    based on the dir/undir constants in the existing direction column

    @param df: input network df that contains a directionality column
    @param existing_direction_column: the name of the existing directionality column
    @param dir_const: the directed edge const
    @param undir_const: the undirected edge const
    @return a df with universal Direction column added back
    """

    df.insert(df.shape[1], "Direction", "NA")

    mask_dir = df[existing_direction_column] == dir_const
    df.loc[mask_dir, "Direction"] = "D"

    mask_undir = df[existing_direction_column] == undir_const
    df.loc[mask_undir, "Direction"] = "U"

    if not df[existing_direction_column].isin([dir_const, undir_const]).all():
        raise ValueError(f"The column '{existing_direction_column}' contains values other than '{dir_const}' and '{undir_const}'")

    return df


def reinsert_direction_col_undirected(df: pd.DataFrame) -> pd.DataFrame:
    """
    adds back a 'Direction' column that puts a columns of 'U's at the end of the provided dataframe

    @param df: input network df that contains a directionality column
    @return a df with Direction column of 'U's added back
    """
    df.insert(df.shape[1], "Direction", "U")

    return df


def reinsert_direction_col_directed(df: pd.DataFrame) -> pd.DataFrame:
    """
    adds back a 'Direction' column that puts a column of 'D's at the end of the provided dataframe

    @param df: input network df that contains directionality column
    @return a df with Direction column of 'D's added back
    """
    df.insert(df.shape[1], "Direction", "D")

    return df
