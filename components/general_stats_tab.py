import streamlit as st

def total_stats_component(df):
    cols2desc = {
        'Reach 1+ (fact)': {'label': 'Охват', 'value': f"{round(df['Reach 1+ (fact)'].mean() // 1000, 2)}k"},
        'Viewable impressions (fact)': {'label': 'Показы', 
            'value': f"{round(df['Viewable impressions (fact)'].mean() // 1000, 2)}k"},
        'Impressions (delta)': {'label': '$\\Delta_{показов}$'},
        'Click (fact)': {'label': 'Клики:', 'value': f"{round(df['Click (fact)'].mean() // 1000, 2)}k"},
        'cost':  {'label': 'Расходы:', 'value': f"RUB {round(df['cost'].mean() // 1000, 2)}k"},
        'cpc': {'label': 'CPC:', 'value': f"RUB {round((df['cost'] / df['Click (fact)']).mean(), 2)}"}
        # 'cum_ret': '$\overline{\\text{cum-ret}}$:'+f"{round(df['cum_ret'].mean() * 100, 2)}%",
        # 'vei': '$\overline{vei}$:'+f"{round(df['vei'].mean() * 100, 2)}%",
    }
    total_cols = list(cols2desc.keys())

    # first row
    cols = st.columns(3)
    for i, col in enumerate(cols):
        cnt = col.container(height=120)
        # adding button linking a metric with its explanation in the docs
        """if total_cols[i] in ['cum_ret','vei']:
            cnt.markdown(f'''
            <div style="display:flex;justify-content:left;align-items:center;margin-bottom:10px;">
                <a style="display:block;width:50%;border-radius:25% 10%;text-decoration:none;color:#adadad;text-align:center;background:#262730;cursor:pointer;" href="/metrics#{total_cols[i]}">
                    ℹ
                </a>
            </div>
             <hr style="margin-bottom:5px;margin-top:5px" />
            ''',unsafe_allow_html=True)"""

        # highlight delta with green
        if total_cols[i] in ['Impressions (delta)']:
            delta = f"{round(df['Impressions (delta)'].mean() * 100, 2)}%"
            delta_than_half = float(delta.strip('%')) > 0
            cnt.markdown(
                cols2desc[total_cols[i]]['label']+
                f'''
                    <h1 style=color:{"#64f57a" if delta_than_half > 0 else "#f56964"};font-weight:100;display:block;position:relative;top:-2.5rem>
                        {("+" if delta_than_half else "")+delta}
                    </h1>
                ''', unsafe_allow_html=True
            )
        else:
            cnt.metric(cols2desc[total_cols[i]]['label'], cols2desc[total_cols[i]]['value'])
            # cnt.markdown(cols2desc[total_cols[i]])
    
    cols_ = st.columns(3)
    for i, col in enumerate(cols_):
        cnt = col.container(height=120)
        cnt.metric(
            cols2desc[total_cols[i+3]]['label'], 
            cols2desc[total_cols[i+3]]['value'],
            help='Для каждой рекламы была сгенерирована \
                сумма затрат из интервала [15k; 500k]' if 'cost' \
                    in total_cols[i+3] else None
        )