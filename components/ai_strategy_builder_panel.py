import streamlit as st

from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml


def render_ai_strategy_builder_panel():
    st.markdown("### 01 — State the thesis")
    st.caption("Describe the idea as you trade it. VectorAlgoAI will show its interpretation before any test is run.")

    market = st.selectbox(
        "Market",
        ["XAUUSD", "NAS100", "US30", "BTCUSD", "ETHUSD"],
        index=0,
        key="ai_market"
    )

    timeframe = st.selectbox(
        "Timeframe",
        ["15m", "1h", "4h", "1d"],
        index=1,
        key="ai_timeframe"
    )

    strategy_text = st.text_area(
        "Describe the strategy in plain English",
        height=132,
        key="ai_text",
        placeholder="Example: Trade NAS100 long when price retests a confirmed 1H support zone after a breakout. Require a bullish rejection candle on 5m. Avoid high-impact news. Risk 0.5% and target 2R."
    )

    if st.button(
        "Create research blueprint", use_container_width=True, type="primary"
    ):

        if not strategy_text.strip():
            st.warning("Please enter a strategy.")
            return

        schema = build_strategy_from_text(
            strategy_text
        )

        generated_yaml = compile_schema_to_yaml(
            schema,
            market=market,
            timeframe=timeframe
        )

        st.session_state["strategy_yaml"] = generated_yaml
        st.session_state["blueprint_schema"] = schema
        st.session_state["blueprint_approved"] = False
        st.rerun()

    schema = st.session_state.get("blueprint_schema")
    if not schema:
        return

    st.markdown("### 02 — Confirm the blueprint")
    st.caption("This is the research contract. Review it carefully—results are only as reliable as the rules being tested.")
    components = schema.get("components", [])
    grouped = {}
    for component in components:
        grouped.setdefault(component.get("category", "other").replace("_", " ").title(), []).append(component.get("component", "rule").replace("_", " ").title())

    base = [("Market", market), ("Timeframe", timeframe)]
    items = base + [(name, ", ".join(values)) for name, values in grouped.items()]
    cols = st.columns(3)
    for index, (label, value) in enumerate(items):
        with cols[index % 3]:
            st.markdown(f'<div class="va-card"><div class="va-card-title">{label}</div><div class="va-card-value">{value}</div></div>', unsafe_allow_html=True)

    if not grouped:
        st.warning("The thesis is still too broad to produce explicit rules. Add the market context, entry trigger, confirmation and risk/exit conditions.")
    else:
        st.markdown('<span class="va-status amber">Review required</span> &nbsp; <span style="color:#94a3b8;font-size:.86rem">Some components may need parameters before the strategy can be considered fully specified.</span>', unsafe_allow_html=True)
        action, detail = st.columns([1, 2])
        with action:
            if st.button("Approve blueprint", type="primary", use_container_width=True):
                st.session_state["blueprint_approved"] = True
                st.success("Blueprint approved. You can now run the evidence test below.")
        with detail:
            with st.expander("Advanced: inspect generated research configuration"):
                st.code(st.session_state.get("strategy_yaml", ""), language="yaml")
