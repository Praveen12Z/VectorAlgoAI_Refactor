import pandas as pd
import streamlit as st


def render_market_fit_panel(results, baseline_trades=0):

    st.subheader(
        "🌍 Market Fit Analyzer"
    )

    if not results:

        if baseline_trades < 30:
            st.warning(
                "Cross-market comparison is locked until the baseline strategy has at least 30 trades."
            )
        else:
            st.warning("No eligible cross-market evidence is available.")

        return

    df = pd.DataFrame(results)

    st.dataframe(
        df,
        use_container_width=True
    )

    best = results[0]

    st.success(
        f"Strongest tested market: "
        f"{best['market']} "
        f"(PF {best['profit_factor']})"
    )
