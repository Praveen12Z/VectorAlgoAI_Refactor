import pandas as pd
import streamlit as st

def render_market_fit_panel(results):

    st.subheader(
        "🌍 Market Fit Analyzer"
    )

    if not results:
        st.warning(
            "No market fit data available."
        )
        return

    df = pd.DataFrame(results)

    st.dataframe(
        df,
        use_container_width=True
    )

    best = results[0]

    st.success(
        f"Best Market: "
        f"{best['market']} "
        f"(PF {best['profit_factor']:.2f})"
    )