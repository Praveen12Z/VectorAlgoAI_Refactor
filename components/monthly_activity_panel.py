import pandas as pd
import streamlit as st


def render_monthly_activity(validation):
    st.subheader("Monthly trade frequency")
    segment = st.selectbox("Frequency sample", ['full', 'development', 'holdout'])
    rows = validation.get(segment, {}).get('metrics', {}).get('monthly_activity', [])
    if not rows:
        st.info("Run a new backtest to generate monthly activity.")
        return
    table = pd.DataFrame(rows)
    assessed = table[table['frequency_target'] != 'Not assessed']
    if len(assessed):
        st.write(f"Average entries per interior month: **{assessed['entries'].mean():.1f}** · "
                 f"Months with 50–60 entries: **{int((assessed['frequency_target'] == '50–60').sum())}/{len(assessed)}**")
    else:
        st.info("No interior calendar months available to assess the monthly target.")
    st.caption("Counts use entry month; net realized P&L uses exit month. Zero-trade months remain visible. Boundary months are excluded from the target summary. Interior months are not a guarantee of complete data coverage. Frequency is not a profitability or readiness score.")
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.download_button("Download monthly activity", table.to_csv(index=False),
        file_name=f'{segment}_monthly_activity.csv', mime='text/csv')
