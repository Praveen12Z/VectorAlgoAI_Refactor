# components/ai_strategy_builder_panel.py

import streamlit as st

from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml


def render_ai_strategy_builder_panel():

    st.subheader("🧠 AI Strategy Builder")

    market = st.selectbox(
        "Market",
        ["XAUUSD", "NAS100", "US30", "BTCUSD", "ETHUSD", "EURUSD", "GBPUSD"],
        index=0,
        key="ai_builder_market",
    )

    timeframe = st.selectbox(
        "Timeframe",
        ["15m", "1h", "4h", "1d"],
        index=1,
        key="ai_builder_timeframe",
    )

    strategy_text = st.text_area(
        "Describe your strategy in plain English",
        placeholder=(
            "Example: Buy Gold when trend is bullish, price pulls back to support, "
            "RSI confirms momentum, avoid FOMC, target 3R."
        ),
        height=160,
        key="ai_strategy_text",
    )

    if st.button("Build Strategy YAML", use_container_width=True):

        if not strategy_text.strip():
            st.warning("Please describe your strategy first.")
            return None

        schema = build_strategy_from_text(strategy_text)

        generated_yaml = compile_schema_to_yaml(
            schema,
            market=market,
            timeframe=timeframe,
        )

        st.success("Universal Strategy Schema generated.")
        st.json(schema)

        st.success("YAML strategy generated.")

        st.code(generated_yaml, language="yaml")

        st.session_state["strategy_yaml"] = generated_yaml
        st.session_state["current_strategy_name"] = "AI Generated Universal Strategy"

        st.info("Generated YAML has been loaded into the Strategy YAML box below.")

        return schema

    return None
