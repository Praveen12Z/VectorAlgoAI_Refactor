import pandas as pd
import streamlit as st


def render_evolution_lab(results):

    st.subheader(
        "🧬 Strategy Evolution Lab"
    )

    if not results:

        st.warning(
            "No evolution results."
        )

        return

    df = pd.DataFrame(results)

    st.dataframe(
        df,
        use_container_width=True
    )

    best = results[0]

    st.success(
        f"""
🏆 Best Candidate

Variant:
{best['variant']}

Market:
{best['market']}

PF:
{best['profit_factor']}

Return:
{best['return_pct']}%
"""
    )
