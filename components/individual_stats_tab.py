import streamlit as st
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import datetime
import plotly.graph_objects as go
import numpy as np

def selector_component(df: pd.DataFrame):
    col1,col2,col3,col4=st.columns(4)
    with col1:
        brand = st.selectbox(
        'Бренд',
        df['Brands'].unique(),2)
    with col2:
        status = st.selectbox(
        'Статус кампании', ['в процессе','истекла'], 1, help='Истекло ли время публикации рекламы')     
    with col3:
        dt_int = st.date_input(
            "Период:",
            (datetime.date(2023, 1, 1), ),
            format="MM.DD.YYYY",
        )
    with col4:
        id_ = st.multiselect(
        'Поиск по ID',
        df['id'].astype(str).unique(),
        [], max_selections=1)
    
    col5,col6,col7=st.columns(3)
    with col5:
        q = st.multiselect(
        'Квартал',
        ['q1', 'q2', 'q3', 'q4'],
        [])
    with col6:
        sites = df['sites'].unique()
        site = st.multiselect(
        'Площадки',
        sites,
        [])
    with col7:
        formats = df['Ad copy format'].unique()
        format = st.multiselect(
        'Формат',
        formats,
        [])
        
    return brand, site, format, status, q, id_, dt_int

def hist_selector_component(df: pd.DataFrame, key: str = None, t = None, **kwargs):
    primaryCol = None
    try:
        isPie = kwargs['isPie']
    except:
        isPie = False
    try:
        _ = kwargs['extra_col']
        metricCols = df.columns[df.columns.str.lower().str.contains(
            r'\%|impres|reach|click|viewa|vei|cum_ret|cost|cpm')]
        groupByCols = df.columns[df.columns.str.lower().str.contains('brands')]
        if t is not None:
            col1,col2 = t.columns([1,1])
        else:
            col1,col2 = st.columns([1,1])
        with col1:
            selectedCol = st.selectbox(
                'Столбец для группировки',
                groupByCols, 
                key=key+'2', 
                format_func=lambda x: f'Столбец "{x}"'
            )
        with col2:
            primaryCol = st.selectbox(
                'Метрика для изучения',
                metricCols, key=key+'1', format_func=lambda x: f'Метрика "{x}"'
            )
    except:
        groupByCols = df.columns[
        (df.nunique().values < 15) & 
        ~df.columns.str.lower().str.contains(
            r'\%|brands|date|cum|vei|duration|skippable|rotation')]
        if t is not None:
            selectedCol = t.selectbox(
                'Столбец для группировки',
                groupByCols, 
                key=key+'2', 
                format_func=lambda x: f'Столбец "{x}"'
            )
        else:
            selectedCol = st.selectbox(
                'Столбец для группировки',
                groupByCols, 
                key=key+'2', 
                format_func=lambda x: f'Столбец "{x}"'
            )

    sorting = None
    if not isPie:
        if t is not None:
            sorting = t.checkbox('Сортировка', key=key+'3')
        else:
            sorting = st.checkbox('Сортировка', key=key+'3')
    
    if primaryCol is None:
        return selectedCol, sorting
    else:
        return selectedCol, sorting, primaryCol

def timeSer_selector_component(df: pd.DataFrame, key: int, t = None):
    groupByCols = df.columns[
        (df.nunique().values < 15) & 
        ~df.columns.str.lower().str.contains(
            r'\%|brands|date|cum|vei|duration|skippable|rotation')]
    if t is not None:
        selectedCol = t.selectbox(
            'Столбец для группировки статистики',
            groupByCols, key=key, format_func=lambda x: f'Столбец "{x}"'
        )
    else:
        selectedCol = st.selectbox(
            'Столбец для группировки статистики',
            groupByCols, key=key, format_func=lambda x: f'Столбец "{x}"'
        )
    return selectedCol

def additionalTimeSer_selector(keys: list, key:int, t = None):
    if t is not None:
        selectedCol = t.selectbox(
            'Столбец для изучения',
            keys, key=key, format_func=lambda x: f'Метрика "{x}"'
        )
    else:
        selectedCol = st.selectbox(
            'Столбец для изучения',
            keys, key=key, index=1, format_func=lambda x: f'Метрика "{x}"'
        )
    return selectedCol

def overview_component(df = None, y = None, x = None, aggCol = None, 
                       diagType = None, title = None, ylabel = None, **kwargs):
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
        y = y.values if len(y) > 1 else y[0]
        fig = go.Figure(go.Funnelarea(
            values = np.repeat(100,4)+np.hstack([[0],np.diff(y)*100]).cumsum() / y[0],
            textinfo='value',
            hovertext=[f'{y_ // 1000}k' for y_ in y],
            labels= ['25%','50%','75%','100%'],
        ))
        fig.update_layout(
        title={
            'text':f'{title} (%)',
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'})
        fig.update_traces(hoverinfo="text", hovertemplate=None)
    elif diagType == 'gauge':
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = x,
            gauge = kwargs['gauge'],
            delta = kwargs['delta'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': title}),
            )
        fig.update_layout(
            autosize=True,
            width=275 if kwargs['size'] == 'sm' else 512,
            height=275 if kwargs['size'] == 'sm' else 512
        )
    elif diagType == 'pie':
        fig = px.pie(df, values=y, names=x,
            title=title,
            hover_data=[x],
            # labels={'lifeExp':'life expectancy'}
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
    elif diagType == 'timeSer':
        fig = px.area(df, x=x, y=y,
              color=aggCol,
              hover_data={x: "|%B %d, %Y"},
              title=title
            )
        fig.update_xaxes(
            dtick="M1",
            ticklabelmode="period",
            tickformat="%b\n%Y",
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="месяц", step="month", stepmode="backward"),
                    dict(count=6, label="полгода", step="month", stepmode="backward"),
                    dict(count=1, label="текущий год", step="year", stepmode="todate"),
                    dict(step="all", label='полностью')
                ])
            ),
        )
        fig.update_traces(
            # line_color='#8b79f2'
        )
        fig.update_layout(
            yaxis_title=y,
            xaxis_title='Временное окно'
        )
        if df[aggCol].astype(str).str.len().max() > 15:
            fig.update_layout(showlegend=False)
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