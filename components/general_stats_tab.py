import streamlit as st

def total_stats_component(df):
    cols2desc = {
        'CTR % (fact)': '$\overline{CTR}$:'+f"{round(df['CTR % (fact)'].mean() * 100, 2)}%",
        'Viewability rate % (fact)': '$\overline{\\text{view-rate}}$:'+f"{round(df['Viewability rate % (fact)'].mean() * 100, 2)}%",
        'cum_ret': '$\overline{\\text{cum-ret}}$:'+f"{round(df['cum_ret'].mean() * 100, 2)}%",
        'Impressions (delta)': '$\overline{\\Delta_{impress}}$:'+f"{round(df['Impressions (delta)'].mean() * 100, 2)}%",
        'vei': '$\overline{vei}$:'+f"{round(df['vei'].mean() * 100, 2)}%",
        'Reach 1+ (fact)': '$\overline{reach}$:'+f"{round(df['Reach 1+ (fact)'].mean() // 1000, 2)}k"
    }
    total_cols = list(cols2desc.keys())
    cols = st.columns(6)
    for i, col in enumerate(cols):
        cnt = col.container(height=120)
        # adding button linking a metric with its explanation in the docs
        if total_cols[i] in ['cum_ret','vei']:
            cnt.markdown(f'''
            <div style="display:flex;justify-content:left;align-items:center;margin-bottom:10px;">
                <a style="display:block;width:50%;border-radius:25% 10%;text-decoration:none;color:#adadad;text-align:center;background:#262730;cursor:pointer;" href="/metrics#{total_cols[i]}">
                    ℹ
                </a>
            </div>
             <hr style="margin-bottom:5px;margin-top:5px" />
            ''',unsafe_allow_html=True)
        cnt.markdown(cols2desc[total_cols[i]])
        