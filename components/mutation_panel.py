import pandas as pd
import streamlit as st


def render_mutation_panel(results):

    st.subheader(
        "🧬 Strategy Mutation Engine"
    )

    if not results:

        st.warning(
            "No mutations available."
        )

        return

    df = pd.DataFrame(results)

    st.dataframe(
        df,
        use_container_width=True
    )

    best = results[0]

    st.success(
        f"🏆 Best Variant: "
        f"{best['name']} "
        f"(PF {best['pf']})"
    )
