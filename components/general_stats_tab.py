import streamlit as st
import plotly.express as px

def timerSerSelector(df):
    metricCols = df.columns[
        df.columns.str.lower().str.contains(
        r'\%|impres|reach|click|viewa|vei|cum_ret|cost|cpm') &
        ~df.columns.str.lower().str.contains(
            r'^\d+\%'
        )
    ]
    metricSelector = st.selectbox(
        'Столбец с метрикой',
        metricCols, 
        format_func=lambda x: f'Метрика "{x}"'
    )
    return metricSelector

def timerSerGraph(df, title):
    fig = px.bar(df, x="Stop date", y=df.columns,
              hover_data={"Stop date": "|%b %d, %Y"},
              title=title)
    fig.update_xaxes(
        dtick="M1",
        tickformat="%b\n%Y")
    st.plotly_chart(fig,theme="streamlit", use_container_width=True)

def hDivider(h: int, p: int):
    return st.markdown(f'''
        <div style="padding:{p}px">
            <div style="
            border-right:1px;
            border-top:none;border-bottom:none;
            border-left:none;border-style:solid;
            border-color:#26282e;position:absolute;
            opacity: 0.33;
            height:{h}px;left:50%;"></div>  
        </div>
    ''', unsafe_allow_html=True)

def changeIouWeight(idx):
    st.session_state['iouWeights'][
        int(idx.replace('wSl',''))
    ] = st.session_state[idx]

def returnWweight(key):
    return st.session_state['iouWeights'][
        int(key.replace('wSl',''))
    ]

def iouWSlider(df):
    brands = df['Brands'].sort_values().unique()
    cols = st.columns(len(brands) // 2)
    for i, col in enumerate(cols):
        k = 'wSl'+str(i)
        col.slider(f'Важность для "{brands[i]}":', min_value=0.0, 
                    max_value=1.0, 
                    value=returnWweight(k), 
                    step=.01, key=k, 
                    on_change=changeIouWeight,
                    args=[k])
        
    nextCols = st.columns(len(brands) - len(brands) // 2)
    for i, col in enumerate(nextCols):
        k = 'wSl'+str(i+len(cols))
        col.slider(f'Важность для "{brands[i+len(cols)]}":', min_value=0.0, 
                    max_value=1.0, 
                    value=returnWweight(k), 
                    step=.01, key=k, 
                    on_change=changeIouWeight,
                    args=[k])



def total_stats_component(df):
    total_cost = round(df['cost'].sum() // 1000, 2)
    cols2desc = {
        'Reach 1+ (fact)': {'label': 'Охват', 'value': f"{round(df['Reach 1+ (fact)'].mean() // 1000, 2)}k"},
        'Viewable impressions (fact)': {'label': 'Показы', 
            'value': f"{round(df['Viewable impressions (fact)'].mean() // 1000, 2)}k"},
        'Impressions (delta)': {'label': '$\\Delta_{показов}$'},
        'Click (fact)': {'label': 'Клики:', 'value': f"{round(df['Click (fact)'].mean() // 1000, 2)}k"},
        'cost':  {'label': ['Расходы (медиана):','Расходы (общие):'], 'value': [f"RUB {round(df['cost'].median() // 1000, 2)}k", 
                                                                                f"RUB {str(total_cost)+'k' if total_cost < 1000 else str(total_cost // 1000)+'m'}"]},
        'cpc': {'label': 'CPC:', 'value': f"RUB {round(df['cpc'].mean(), 2)}"}
        # 'cum_ret': '$\overline{\\text{cum-ret}}$:'+f"{round(df['cum_ret'].mean() * 100, 2)}%",
        # 'vei': '$\overline{vei}$:'+f"{round(df['vei'].mean() * 100, 2)}%",
    }
    total_cols = list(cols2desc.keys())

    # first row
    cols = st.columns(3)
    for i, col in enumerate(cols):
        print(col)
        cnt = col.container(height=120)
        # highlight delta with green
        if total_cols[i] in ['Impressions (delta)']:
            delta = f"{round(df['Impressions (delta)'].mean() * 100, 2)}%"
            delta_than_half = float(delta.strip('%')) > 0
            cnt.markdown(
                cols2desc[total_cols[i]]['label']+
                f'''
                    <h1 style=color:{"#64f57a" if delta_than_half > 0 else "#f56964"};font-weight:100;display:block;position:relative;top:-2.4rem>
                        {("+" if delta_than_half else "")+delta}
                    </h1>
                ''', unsafe_allow_html=True
            )
        else:
            cnt.metric(cols2desc[total_cols[i]]['label'], cols2desc[total_cols[i]]['value'])
    
    cols_ = st.columns(3)
    for i, col in enumerate(cols_):
        cnt = col.container(height=150)
        if total_cols[i+3] in ['cost']:
            cnt.metric(cols2desc[total_cols[i+3]]['label'][0], 
                       cols2desc[total_cols[i+3]]['value'][0],
                       help='Для каждой рекламы была сгенерирована \
                сумма затрат из интервала [15k; 500k]')
            cnt.metric(cols2desc[total_cols[i+3]]['label'][1], 
                       cols2desc[total_cols[i+3]]['value'][1])
        else:
            
            cnt.metric(
                cols2desc[total_cols[i+3]]['label'], 
                cols2desc[total_cols[i+3]]['value'],
            )