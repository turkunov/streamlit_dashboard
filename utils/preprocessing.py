import pandas as pd
import numpy as np
from datetime import datetime
from pandas.api.types import is_integer_dtype, is_float_dtype

def preprocess_percentage_cols(df: pd.DataFrame):
    obj_cols = df.columns[
        (df.dtypes.values == 'O') & 
        (
            df.columns.str.contains('%') |
            df.columns.isin(['Impressions (delta)'])
        )
    ].values
    df[obj_cols] = df[obj_cols].apply(
        lambda x: x.str.rstrip('%').astype('float64') / 100)
    return df

def strDateToDatetime(df: pd.DataFrame):
    df['Start date'] = pd.to_datetime(df['Start date'], format='%d.%m.%Y')
    df['Stop date'] = pd.to_datetime(df['Stop date'], format='%d.%m.%Y')
    return df


def replaceAndRemNaN(df: pd.DataFrame):
    df = df.loc[:, ~((df.isna().sum().values / df.shape[0]) >= .9)]
    df = df[~df['id'].isna()]
    null_cols = df.isna() | df.isnull()
    for col in df.columns[null_cols.sum(axis=0) > 0]:
        if is_integer_dtype(df[col]) or is_float_dtype(df[col]):
            df[col].replace(np.nan, df[col].mean(), inplace=True)
        else:
            df[col].replace(np.nan, df[col].mode()[0], inplace=True)
    return df

def filter_df(df: pd.DataFrame, b,si,f,st,q,i):
    """
    b: str
     - brand name

    si: list
     - platform names

    f: list
     - ad format types

    st: list
     - ad status

    q: list
     - ad publication quaters

    i: str
     - ad ID
    """
    if len(i) == 0:
        qs = list(range(1,13))
        qs = {f'q{(i//3+1)}': qs[i:i+3] for i in range(0,len(qs),3)}
        qs = sum([qs[q_i] for q_i in q],[])
        df = df[
            (df['Brands'] == b) &
            (df['sites'].isin(si) if len(si) > 0 else True) &
            (df['Ad copy format'].isin(f) if len(f) > 0 else True) &
            (
                (np.isin(df['Start date'].dt.month,qs) |
                np.isin(df['Stop date'].dt.month,qs)) if len(q) > 0 \
                else True
            )
        ]
        return df
    return df[
        df['id'] == int(i)
    ]
