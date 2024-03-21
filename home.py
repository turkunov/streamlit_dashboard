import streamlit as st
from streamlit.components.v1 import html
import plotly.express as px
import numpy as np
from components.general_stats_tab import total_stats_component
from components.individual_stats_tab import selector_component, overview_component, hist_selector_component
from utils.preprocessing import filter_df, strDateToDatetime, preprocess_percentage_cols, \
    replaceAndRemNaN, generateAdCosts, distinguishBadRows, highlightRows
from utils.custom_metrics import cumret, vei
import pandas as pd
from datetime import datetime

def full_df_preprocess(df):
    # preprocessing of data
    df = replaceAndRemNaN(df)
    df = strDateToDatetime(df)
    df = preprocess_percentage_cols(df)

    # adding auxiliary metrics to the table
    df = cumret(df)
    df = vei(df)
    df = generateAdCosts(df)

    return df

st.set_page_config(
    page_title='H&N Dashboard',
    page_icon='📊'
)

df = None # needed init. If dataframe is not uploaded -> avoid plotting
if 'relRequired' not in st.session_state:
    st.session_state['relRequired'] = False
if 'data' not in st.session_state:
    st.session_state['data'] = None

if st.session_state['data'] is None: # this is needed to keep track of df between page switches
    maincol, warncol = st.columns(2)
    with maincol:
        if st.session_state['relRequired']:
            st.header('Загрузите файл для создания дашборда ⤵')
            uploaded_file = st.file_uploader(label='', label_visibility='collapsed', type='csv')
            if uploaded_file is not None:
                if uploaded_file.name.split('.')[1] == 'csv':
                    df=pd.read_csv(uploaded_file)
                    st.session_state['data'] = full_df_preprocess(df)
                    st.rerun()
                else: # if file is not CSV
                    errormsg = "<script>alert('Загрузите файл с расширением .csv')</script>"
                    html(errormsg, height=0, width=0)
        else:
            df=pd.read_csv('./auxiliary/data.csv')
            st.session_state['data']=full_df_preprocess(df)
            st.rerun()
    with warncol:
        st.warning('''
        Обратите внимание, что формат 
        входных данных должен соответствовать примеру:
        ''', icon='✴')
        st.dataframe(pd.read_csv('./auxiliary/data.csv').head(4))
else:
    df = st.session_state['data']
    if st.button("Очистить дашборд", type="primary"):
        st.session_state['data'] = None
        st.session_state['relRequired'] = True
        st.rerun()

def main():
    st.sidebar.markdown(f'''
        <p style='text-align: center; color: gray;'>
            (c) <a href="https://github.com/turkunov">@turkunov</a> // {datetime.now().year}
        </p>
    ''', unsafe_allow_html=True)
    tab_main, tab_private = st.tabs(["Дашборд по общим данным", "Дашборд по брендам и кампаниям"])
    with tab_main:
        if df is not None:
            total_stats_component(df)
            badRows2Errs = df.apply(distinguishBadRows, axis=1)
            tooltips_df = pd.DataFrame(badRows2Errs.values)
            tooltips_df.columns = ['errors']
            general_df = pd.concat([tooltips_df, df], axis=1)
            st.data_editor(
                general_df.style \
                .apply(lambda r: 
                       highlightRows(r,'errors','#f06451'),
                    axis=1),
                column_config={
                    "errors": st.column_config.ListColumn(
                        "Ошибки ⓘ",
                        help="Столбец подсвечивается красным, если в одном из \
                            полей допущена ошибка. Выводит список найденных \
                                ошибок, которые необходимо исправить.",
                        width="medium",
                    ),
                },
                num_rows="dynamic"
            )
    with tab_private:
        if df is not None:
            brand, site, format, status, q, id_, dt_int = selector_component(df)
            filtered_df = filter_df(df,brand,site,format,status,q,id_,
                                    dt_int)
            total_stats_component(filtered_df)
            con = st.container(height=512)
            if len(id_) == 0:
                individual_tabs = ['Охват', 'CTR %', 'Просмотры']
                tab2metric = {
                    'охват': 'reach',
                    'ctr %': 'ctr',
                    'просмотры': 'view|impression'
                }
                con_tabs = con.tabs(individual_tabs)
                for i, tab in enumerate(con_tabs):
                    groupbyCol = df.columns[df.columns.str.lower().str.contains(
                        tab2metric[individual_tabs[i].lower()])]
                    if len(groupbyCol) > 1: # if it is related to views
                        # views funnel
                        tab.plotly_chart(
                            overview_component(y=filtered_df[groupbyCol[
                                groupbyCol.str.contains('Views')]].mean(axis=0),
                                title='Воронка просмотров', 
                                diagType='funnel'),
                            theme="streamlit", use_container_width=True
                        )

                        # viewablity impressions+rate dists on boxplot
                        gpc = groupbyCol[groupbyCol.str.lower().str.contains('viewab')].values
                        cols = tab.columns(2)
                        for i, col in enumerate(cols):
                            col.plotly_chart(
                                overview_component(filtered_df, gpc[i],
                                    title=f"Распределение :: {gpc[i].strip('(fact)')}", 
                                    diagType='box'),
                                theme="streamlit", use_container_width=True
                            )
                        
                        # viewablity impressions+rate plotting historgrams
                        selectedCol, sorting = hist_selector_component(
                            filtered_df, gpc[0]+str(i), tab)
                        cols_ = tab.columns(2)
                        for i, col in enumerate(cols_):
                            df_for_hist = pd.DataFrame(
                                filtered_df.groupby(selectedCol)[gpc[i]].mean()
                            ).reset_index()
                            if sorting:
                                df_for_hist = df_for_hist.sort_values(by=gpc[i])
                            col.plotly_chart(
                                overview_component(df_for_hist, gpc[i], selectedCol,
                                    title=f'{gpc[i]} по {selectedCol}', 
                                    diagType='hist'),
                                theme="streamlit", use_container_width=True
                            )

                        # impressions gauge plot
                        impressionCols = ['Impression (plan)', 'Impressions (fact)', 'Выполнение плана показов']
                        viewCols = ['Viewable impressions (fact)', 'Viewability rate % (fact)', 'Видимость показов']
                        tab.plotly_chart(
                            overview_component(
                                x=filtered_df[impressionCols[1]].mean() // 1000,
                                diagType='gauge',
                                title=impressionCols[2],
                                delta={'reference': filtered_df[impressionCols[0]].mean() // 1000},
                                gauge={'axis': {'range': [None,filtered_df[impressionCols[0]].mean() // 1000]}}
                            )
                        )
                        # views gauge plot
                        tab.plotly_chart(
                            overview_component(
                                x=(filtered_df[viewCols[1]]*filtered_df[viewCols[0]]).mean() // 1000,
                                diagType='gauge',
                                title=viewCols[2],
                                delta={'reference':filtered_df[viewCols[0]].mean() // 1000},
                                gauge={'axis': {'range': [None,filtered_df[viewCols[0]].mean() // 1000]}}
                            )
                        )
                            
                    else: # if it is CTR or reach
                        gpc = groupbyCol.values[0]
                        tab.plotly_chart(
                            overview_component(filtered_df, gpc,
                                title=f'Распределение :: {gpc}', 
                                diagType='box'),
                            theme="streamlit", use_container_width=True
                        )

                        # plotting historgrams
                        selectedCol, sorting = hist_selector_component(
                            filtered_df, gpc+str(i), tab)
                        df_for_hist = pd.DataFrame(
                            filtered_df.groupby(selectedCol)[gpc].mean()
                        ).reset_index()
                        if sorting:
                            df_for_hist = df_for_hist.sort_values(by=gpc)
                        tab.plotly_chart(
                            overview_component(df_for_hist, gpc, selectedCol,
                                title=f'{gpc}, сгруппированный по {selectedCol}', 
                                diagType='hist'),
                            theme="streamlit", use_container_width=True
                        )
            else:
                filtered_df = filtered_df[filtered_df['id'] == int(id_)]
                if filtered_df.shape[0] > 0:
                    groupbyCol = df.columns[df.columns.str.lower().str.contains('views')]
                    con.plotly_chart(
                        overview_component(y=filtered_df.loc[:,groupbyCol.values].values,
                            title=f'Воронка просмотров', 
                            diagType='funnel'),
                        theme="streamlit", use_container_width=True
                    )
                else:
                    con.header(f'Рекламная кампания с ID `{id_}` не найдена в датасете')
            

if __name__ == '__main__':
    main()