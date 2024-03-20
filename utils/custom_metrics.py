import numpy as np
import pandas as pd
import scipy.stats as st

def sites_to_onehot(vals, ohmatrix, idxarr):
    return ohmatrix[
        [idxarr[brand] for brand in vals]
    ].sum(axis=0)

def cumret(df: pd.DataFrame):
    """
    Расчет кумулятивного изменения в просмотрах
    """
    views_info = df.loc[:, df.columns.str.contains('Views')].T
    ret_change = views_info.pct_change(fill_method=None)
    cum_ret_change = np.expm1(np.log1p(ret_change).cumsum())
    df = pd.concat([df, cum_ret_change[-1:].T], axis=1)
    df.columns = df.columns.tolist()[:-1] + ['cum_ret']
    df['cum_ret'] += 1 # [-1; 0] -> [0; 1]
    return df

def iou(df: pd.DataFrame, w: np.ndarray):
    """
    Расчет Index of Unrepresentatibility

    df: pd.DataFrame
        - изначальная таблица с данными
    w: np.ndarray
        - Матрица W~U([0, 1]) весов относительно каждого бренда, которая
        выражает важность каждого бренда в его присутствии на платформах.
        Определяется пользователем через интерфейс.
    """
    # расчет T_i
    indexing_array = {site: index for index, site in enumerate(df['sites'].unique())}
    brands_onehot_matrix = np.eye(len(indexing_array))
    brand_presence = df.groupby('Brands')['sites'].unique()
    # One-Hot энкодинг сайтов относительно брендов
    brand_presence = brand_presence.apply(lambda x: sites_to_onehot(
        x,brands_onehot_matrix,indexing_array)).to_frame()
    brand_presence = pd.DataFrame(
        np.vstack(brand_presence['sites'].values), 
        columns=indexing_array.keys(),
        index=brand_presence.index.values
    )
    total_presence = brand_presence.sum(axis=1)

    # расчет T_weighted
    w += 1e-10
    fracs = total_presence / total_presence.sum()
    weighted_presence = total_presence ** (1 - w * fracs)

    # получение доверительного интервала
    alpha = .9
    CI = st.t.interval(
        confidence=alpha, 
        df=weighted_presence.shape[0]-1, 
        loc=np.mean(weighted_presence), 
        scale=np.std(weighted_presence) / np.sqrt(weighted_presence.shape[0]) # SE
    ) 

    # если один из брендов ниже эксремального значения (за пределами 90% значений)
    if np.any(weighted_presence < CI[0]): 
        return np.log10(brand_presence.shape[1] / (total_presence + 1e-12)) # расчет IOU
     
def vei(df: pd.DataFrame):
    """
    Viewer Engagement Index
    """
    try:
        df['vei'] = df['CTR % (fact)'] * df['Viewability rate % (fact)'] * df['cum_ret'] ** (df['Skippable'] != 'unskippable')
    except:
        df['vei'] = 0
    return df