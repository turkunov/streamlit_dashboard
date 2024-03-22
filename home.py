import streamlit as st
from streamlit.components.v1 import html
import plotly.express as px
import numpy as np
from components.general_stats_tab import total_stats_component
from components.individual_stats_tab import selector_component, overview_component, \
    hist_selector_component, timeSer_selector_component, additionalTimeSer_selector
from utils.preprocessing import filter_df, strDateToDatetime, preprocess_percentage_cols, \
    replaceAndRemNaN, generateAdCosts, distinguishBadRows, highlightRows
from utils.scrapers import holidays_lookup
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

@st.cache_data  # 👈 Add the caching decorator
def get_holidays():
    df = holidays_lookup()
    return df

holidays_df = get_holidays()

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
            df=pd.read_csv('data.csv')
            st.session_state['data']=full_df_preprocess(df)
            st.rerun()
    with warncol:
        st.warning('''
        Обратите внимание, что формат 
        входных данных должен соответствовать примеру:
        ''', icon='✴')
        st.dataframe(pd.read_csv('data.csv').head(4))
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
            
            background_col = general_df.keys()[12:36]
            general_df = general_df.style.background_gradient(cmap='YlGn', subset=background_col)
            st.write("### Обзор", general_df)

            brands = df['Brands'].unique()
            
            tab1, tab2 = st.tabs(["CTR", "Viewable impressions"])
            with tab1:
                brand_ctr_tmp = []
                for brand in brands:
                    value = df[df.Brands == brand]["CTR % (fact)"].mean()
                    brand_ctr_tmp.append(value)

                brands_ctr = pd.DataFrame({'brands': brands, 'value': brand_ctr_tmp})
                fig_ctr = px.bar(brands_ctr, x='brands', y='value')
                st.plotly_chart(fig_ctr, theme="streamlit", use_container_width=True)



            with tab2:
                brands_impressions_tmp = []
                for brand in brands:
                    value = df[df.Brands == brand]["Viewable impressions (fact)"].sum()
                    brands_impressions_tmp.append(value)

                brands_impressions = pd.DataFrame({'brands': brands, 'value': brands_impressions_tmp})

                fig_ctr_impressions = px.pie(brands_impressions, values='value', names='brands')
                st.plotly_chart(fig_ctr_impressions, theme="streamlit", use_container_width=True)




    with tab_private:
        if df is not None:
            brand, site, format, status, q, id_, dt_int = selector_component(df)
            filtered_df = filter_df(df,brand,site,format,status,q,id_,
                                    dt_int)
            total_stats_component(filtered_df)
            con = st.container(height=700)
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

                        #time series plot
                        tsCol1, tsCol2 = tab.columns(2)
                        with tsCol1:
                            timeCol = timeSer_selector_component(filtered_df,i)
                        with tsCol2:
                            mainTimeCol = additionalTimeSer_selector(groupbyCol,i+1)
                        tab.plotly_chart(
                            overview_component(filtered_df, mainTimeCol, 'Start date',
                                timeCol,diagType='timeSer',
                                title=f'Распределение {mainTimeCol} по датам', 
                            ),
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
                        
                        tab.divider()
                        # impressions gauge plot
                        impressionCols = ['Impression (plan)', 'Impressions (fact)', 'Выполнение плана показов']
                        viewCols = ['Viewable impressions (fact)', 'Viewability rate % (fact)', 'Видимость показов']
                        cnt = tab.container(height=300,border=False)
                        gaugeCol1, gaugeCol2 = cnt.columns(2)
                        with gaugeCol1:
                            st.plotly_chart(
                                overview_component(
                                    x=filtered_df[impressionCols[1]].mean() // 1000,
                                    diagType='gauge',
                                    title=impressionCols[2],
                                    delta={'reference': filtered_df[impressionCols[0]].mean() // 1000},
                                    gauge={'axis': {'range': [None,filtered_df[impressionCols[0]].mean() // 1000]}},
                                    size='sm'
                                )
                            )
                        # views gauge plot
                        with gaugeCol2:
                            st.plotly_chart(
                                overview_component(
                                    x=(filtered_df[viewCols[1]]*filtered_df[viewCols[0]]).mean() // 1000,
                                    diagType='gauge',
                                    title=viewCols[2],
                                    delta={'reference':filtered_df[viewCols[0]].mean() // 1000},
                                    gauge={'axis': {'range': [None,filtered_df[viewCols[0]].mean() // 1000]}},
                                    size='sm'
                                )
                            )
                            
                    else: # if it is CTR or reach
                        gpc = groupbyCol.values[0]
                        # time series graph
                        timeCol = timeSer_selector_component(filtered_df,i,tab)
                        tab.plotly_chart(
                            overview_component(filtered_df, gpc, 'Start date',
                                timeCol,diagType='timeSer',
                                title=f'Распределение {gpc} по датам', 
                            ),
                            theme="streamlit", use_container_width=True
                        )
                        # overall dist graph
                        tab.plotly_chart(
                            overview_component(filtered_df, gpc,
                                title=f'Общее распределение {gpc}', 
                                diagType='box'),
                            theme="streamlit", use_container_width=True
                        )
                        tab.divider()
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
                if filtered_df.shape[0] > 0:
                    groupbyCol = df.columns[df.columns.str.lower().str.contains('views')]
                    con.plotly_chart(
                        overview_component(y=filtered_df.loc[:,groupbyCol.values].values,
                            title=f'Воронка просмотров', 
                            diagType='funnel'),
                        theme="streamlit", use_container_width=True
                    )

                    impressionCols = ['Impression (plan)', 'Impressions (fact)', 'Выполнение плана показов']
                    viewCols = ['Viewable impressions (fact)', 'Viewability rate % (fact)', 'Видимость показов']
                    cnt = con.container(height=300)
                    gaugeCol1, gaugeCol2 = cnt.columns(2)
                    with gaugeCol1:
                        st.plotly_chart(
                            overview_component(
                                x=filtered_df[impressionCols[1]].values[0] // 1000,
                                diagType='gauge',
                                title=impressionCols[2],
                                delta={'reference': filtered_df[impressionCols[0]].values[0] // 1000},
                                gauge={'axis': {'range': [None,filtered_df[impressionCols[0]].values[0] // 1000]}},
                                size='sm'
                            )
                        )
                    # views gauge plot
                    with gaugeCol2:
                        st.plotly_chart(
                            overview_component(
                                x=(filtered_df[viewCols[1]]*filtered_df[viewCols[0]]).values[0] // 1000,
                                diagType='gauge',
                                title=viewCols[2],
                                delta={'reference':filtered_df[viewCols[0]].values[0] // 1000},
                                gauge={'axis': {'range': [None,filtered_df[viewCols[0]].values[0] // 1000]}},
                                size='sm'
                            )
                        )
                else:
                    con.header(f'Рекламная кампания с ID `{id_}` не найдена в датасете')
        
            # extra metrics
            col1,col2 = tab_private.columns(2)
            with col1:
                cont = st.container(height=317)
                filtered_holidays = holidays_df[
                    (holidays_df['date'].dt.month.isin(filtered_df['Start date'].dt.month.values))]
                filtered_holidays['date'] = filtered_holidays['date'].dt.strftime('%d/%m')
                filtered_holidays.columns=['Праздник','Дата (д/м)']
                cont.markdown('Праздники, приходящиеся на кампанию(и):')
                cont.data_editor(filtered_holidays.set_index('Дата (д/м)'),
                    use_container_width=True)
            with col2:
                cont_1 = st.container(height=150)
                veiIndex = round(filtered_df['vei'].mean()*100,2) if len(id_) == 0 \
                      else round(filtered_df['vei'].values[0]*100,2)
                cumretIndex = round(filtered_df['cum_ret'].mean()*100,2) if len(id_) == 0 \
                      else round(filtered_df['cum_ret'].values[0]*100,2)
                cont_1.metric('$vei$',f"{veiIndex}%")
                cont_1.markdown(f'''
                    <div style="display:flex;justify-content:right;align-items:center;margin-bottom:10px;position:relative;top:-5.5rem;">
                        <a style="display:block;width:10%;border-radius:25% 10%;text-decoration:none;color:#adadad;text-align:center;background:#262730;cursor:pointer;" href="/metrics#vei">
                            ℹ
                        </a>
                    </div>
                ''',unsafe_allow_html=True)

                cont_2 = st.container(height=150)
                cont_2.metric('cum_ret',f"{cumretIndex}%")
                cont_2.markdown(f'''
                    <div style="display:flex;justify-content:right;align-items:center;margin-bottom:10px;position:relative;top:-5.5rem;">
                        <a style="display:block;width:10%;border-radius:25% 10%;text-decoration:none;color:#adadad;text-align:center;background:#262730;cursor:pointer;" href="/metrics#cum-ret">
                            ℹ
                        </a>
                    </div>
                ''',unsafe_allow_html=True)

if __name__ == '__main__':
    main()