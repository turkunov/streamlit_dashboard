import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import numpy as np

def selector_component(df: pd.DataFrame):
    col1,col2,col3=st.columns(3)
    with col1:
        brand = st.selectbox(
        'Бренд',
        df['Brands'].unique())
    with col2:
        status = st.selectbox(
        'Статус', ['запущена','остановлена','приостановлена'])     
    with col3:
        id_ = st.text_input('Поиск по ID',max_chars=df['id'].astype('str').str.len().max())

    col4,col5,col6=st.columns(3)
    with col4:
        q = st.multiselect(
        'Квартал',
        ['q1', 'q2', 'q3', 'q4'],
        [])
    with col5:
        sites = df['sites'].unique()
        site = st.multiselect(
        'Площадки',
        sites,
        [])
    with col6:
        formats = df['Ad copy format'].unique()
        format = st.multiselect(
        'Формат',
        formats,
        [])
        
    return brand, site, format, status, q, id_

def hist_selector_component(df: pd.DataFrame, key: int, t):
    groupByCols = df.columns[
        (df.nunique().values < 15) & 
        ~df.columns.str.contains(r'\%|Brands|date')]
    col1,col2,col3 = t.columns([1,1,1])
    sortOrder = None
    with col1:
        selectedCol = t.selectbox(
            'Выберите столбец для группировки',
            groupByCols, key=key+'1', format_func=lambda x: f'Столбец "{x}"'
        )
    with col2:
        sorting = t.checkbox('Сортировка', key=key+'2')
    if sorting:
        with col3:
            sortOrder = t.checkbox('Восходящая сортировка', key=key+'3')
    return selectedCol, sorting, sortOrder

def overview_component(df = None, y = None, x = None, aggCol = None, 
                       diagType = None, title = None, ylabel = None):
    if diagType == 'box':
        fig = px.box(df[y], 
            title=title, 
            hover_name='ID: '+df['id'].astype('str'),
            points="all")
        fig.update_layout(
            yaxis_title=y,
            xaxis_title=''
        )
    elif diagType == 'funnel':
        fig = px.funnel_area(
            names=['25%','50%','75%','100%'],
            values=y if len(y) > 1 else y[0],
            title=title)
    elif diagType == 'hist':
        fig = px.bar(
            df, x=x, y=y, title=title, color=x
        )
        fig.update_layout(
            yaxis_title=ylabel,
            xaxis_title='',
            xaxis_type='category',
            # make tick labels invisible under certain length
            # thershold
            xaxis = go.XAxis(
                showticklabels=(not (df[x].astype(str).str.len() > 10).any())
            ),
        )
    return fig