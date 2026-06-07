# components/ai_strategy_builder_panel.py

import streamlit as st
from core.ai_strategy_builder import build_strategy_from_text


def render_ai_strategy_builder_panel():

    st.subheader("🧠 AI Strategy Builder")

    strategy_text = st.text_area(
        "Describe your strategy in plain English",
        placeholder=(
            "Example: Buy Gold when trend is bullish, price pulls back to support, "
            "RSI confirms momentum, avoid FOMC, target 3R."
        ),
        height=160,
    )

    if st.button("Build Universal Strategy", use_container_width=True):

        if not strategy_text.strip():
            st.warning("Please describe your strategy first.")
            return None

        schema = build_strategy_from_text(strategy_text)

        st.success("Universal Strategy Schema generated.")

        st.json(schema)

        return schema

    return None
