"""
Author: Neha Talluri
07/19/23

Methods for converting/creating the universal input and universal output
"""

import pandas as pd


def convert_undirected_to_directed(df: pd.DataFrame) -> pd.DataFrame:
    """
    turns a graph into a fully directed graph
    - turns every unidirected edges into a bi-directed edge
    - with bi-directed edges, we are not loosing too much information because the relationship of the undirected egde is still preserved

   * A user must keep the Direction column when using this function

    @param df: input network df of edges, weights, and directionality
    @return a dataframe with no undirected edges in Direction column
    """

    mask = df['Direction'] == 'U'
    new_df = df[mask].copy(deep=True)
    new_df['Interactor1'], new_df['Interactor2'] = new_df['Interactor2'], new_df['Interactor1']
    new_df['Direction'] = 'D'
    df.loc[mask, 'Direction'] = 'D'
    df = pd.concat([df, new_df], ignore_index=True)

    print("convert_undirected_to_directed")
    print(df)

    return df


def convert_directed_to_undirected(df: pd.DataFrame) -> pd.DateOffset:
    """
    turns a graph into a fully undirected graph
    - turns all the directed edges directly into undirected edges
    - we will loose any sense of directionality and the graph won't be inherently accurate, but the basic relationship between the two connected nodes will still remain intact.

    * A user must keep the Direction column when using this function

    @param df: input network df of edges, weights, and directionality
    @return a dataframe with no directed edges in Direction column
    """

    df["Direction"] = "U"

    print("convert_directed_to_undirected")
    print(df)

    return df


def add_constant(df: pd.DataFrame, new_col_name: str, const: str) -> pd.DataFrame:
    """
    adds a constant at the end of the input dataframe that is needed inbetween columns for a specifc algorithm

    @param df: input network df of edges, weights, and directionality
    @param new_col_name: the name of the new column
    @param const: some type of constant needed in the df
    @return a df with a new constant added to every row
    """

    df.insert(df.shape[1], new_col_name, const)

    print("add_constant")
    print(df)

    return df


def add_directionality_constant(df: pd.DataFrame,  col_name: str, dir_const: str, undir_const: str) -> pd.DataFrame:
    """
    deals with adding in directionality constants for mixed graphs that aren't using the universal input directly

    * user must keep the Direction column when using the function

    @param df: input network df of edges, weights, and directionality
    @param col_name: the name of the new column
    @param dir_const: the directed edge sep
    @param undir_const: the undirected edge sep
    @return a df converted to show directionality differently
    """
    df.insert(df.shape[1], col_name, dir_const)
    mask = df['Direction'] == 'U'
    df.loc[mask, col_name] = undir_const

    print("add_directionality_constant")
    print(df)

    return df

def readd_direction_col_mixed(df: pd.DataFrame, existing_direction_column: str, dir_const: str, undir_const: str) -> pd.DataFrame:
    """
    readds a 'Direction' column that puts a 'U' or 'D' at the end of provided dataframe
    based on the dir/undir constants in the existing direction column

    *user must keep the existing direction column when using the function

    @param df: input network df that contains directionality
    @param existing_direction_column: the name of the existing directionality column
    @param dir_const: the directed edge sep
    @param undir_const: the undirected edge sep
    @return a df with universal Direction column added back
    """

    df.insert(df.shape[1], "Direction", "D")

    mask_undir = df[existing_direction_column] == undir_const
    df.loc[mask_undir, "Direction"] = "U"

    # mask_dir = df[existing_direction_column] == dir_const
    # df.loc[mask_dir, "Direction"] = "D"

    print("readd_direction_col_mixed")
    print(df)

    return df

def readd_direction_col_undirected(df: pd.DataFrame) -> pd.DataFrame:
    """
    readds a 'Direction' column that puts a columns of 'U's at the end of the provided dataframe

    @param df: input network df that contains directionality
    @return a df with Direction column of 'U's added back
    """
    df.insert(df.shape[1], "Direction", "U")

    print("readd_direction_col_undirected")
    print(df)

    return df

def readd_direction_col_directed(df: pd.DataFrame) -> pd.DataFrame:
    """
    readds a 'Direction' column that puts a column of 'D's at the end of the provided dataframe

    @param df: input network df that contains directionality
    @return a df with Direction column of 'D's added back
    """
    df.insert(df.shape[1], "Direction", "D")

    print("readd_direction_col_directed")
    print(df)

    return df
