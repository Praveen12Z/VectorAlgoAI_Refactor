# components/mutation_panel.py

import pandas as pd
import streamlit as st


def render_mutation_panel(results):
    st.subheader("🧬 Strategy Mutation Engine")

    if not results:
        st.warning("No mutation results available.")
        return

    df = pd.DataFrame(results)

    st.dataframe(
        df,
        use_container_width=True
    )

    best = results[0]

    st.success(
        f"🏆 Best Variant: {best['variant']} "
        f"(PF {best['profit_factor']}, Return {best['return_pct']}%)"
    )

    st.caption(
        "Mutation Engine V2 is rule-based. Later versions will mutate universal strategy components, "
        "including price action, support/resistance, regime filters, news filters, and risk logic."
    )
