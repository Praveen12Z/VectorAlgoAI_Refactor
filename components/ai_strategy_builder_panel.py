import streamlit as st

from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml


def render_ai_strategy_builder_panel():

    st.subheader("🧠 AI Strategy Builder")

    market = st.selectbox(
        "Market",
        ["XAUUSD", "NAS100", "US30", "BTCUSD", "ETHUSD"],
        index=0
    )

    timeframe = st.selectbox(
        "Timeframe",
        ["15m", "1h", "4h", "1d"],
        index=1
    )

    strategy_text = st.text_area(
        "Describe your strategy in plain English",
        height=150
    )

    if st.button("Build Strategy YAML"):

        schema = build_strategy_from_text(
            strategy_text
        )

        st.json(schema)

        generated_yaml = compile_schema_to_yaml(
            schema,
            market,
            timeframe
        )

        st.code(
            generated_yaml,
            language="yaml"
        )

        st.session_state["strategy_yaml"] = generated_yaml
