#
# Tobias Rubel | rubelato@reed.edu
# CompBio
#
# This file contains routines which are commonly used by other programs in this directory.

import os
import pandas as pd

#reading files

def read_df(path:str,csv:str) -> pd.DataFrame:
    """
    :csv     name of csv to open
    :path    path where csv is located
    :returns csv in dataframe format
    """
    return pd.read_csv(os.path.join(path,csv))

def write_df(df:pd.DataFrame,path:str,csv:str) -> None:
    """
    :df          dataframe
    :path        path where csv should be written
    :csv         name of csv file to write to
    :returns     nothing
    :side-effect writes dataframe to csv 
    """
    df.to_csv(os.path.join(path,csv))
