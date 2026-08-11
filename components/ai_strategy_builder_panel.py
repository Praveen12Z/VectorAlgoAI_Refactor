import streamlit as st
import yaml

from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.research_contract import strategy_contract_issues


def render_ai_strategy_builder_panel(active_stage: str = "thesis"):
    """Render either the thesis editor or the separate blueprint review page."""
    if active_stage == "thesis":
        _render_thesis_editor()
    elif active_stage == "blueprint":
        _render_blueprint()
    else:
        st.info("Use Thesis and Blueprint to define the research contract, then continue to this stage.")


def _render_thesis_editor():
    st.markdown("### 01 — State the thesis")
    st.caption("Describe the idea as you trade it. You will review and approve the interpretation before anything is tested.")
    editor, context = st.columns([1.7, 1], gap="large")
    with editor:
        strategy_text = st.text_area(
            "Your trading idea",
            height=205,
            key="ai_text",
            placeholder="Example: Trade NAS100 long when price retests a confirmed 1H support zone after a breakout. Require a bullish rejection candle on 5m. Avoid high-impact news. Risk 0.5% and target 2R."
        )
    with context:
        st.markdown('<div class="va-card"><div class="va-card-title">Research principle</div><div class="va-card-value">No backtest runs until the logic is explicit, inspectable and approved by you.</div></div>', unsafe_allow_html=True)
        st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)
        market = st.selectbox("Market", ["NAS100", "XAUUSD", "US30", "BTCUSD", "ETHUSD"], key="ai_market")
        timeframe = st.selectbox("Primary timeframe", ["15m", "1h", "4h", "1d"], index=1, key="ai_timeframe")

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
        st.session_state["active_workspace_stage"] = "blueprint"
        st.rerun()


def _render_blueprint():
    st.markdown("### 02 — Confirm the blueprint")
    st.caption("This is the research contract. Results are only as reliable as the rules being tested.")
    schema = st.session_state.get("blueprint_schema")
    if not schema:
        st.info("There is no blueprint yet. Start by describing the strategy in the Thesis stage.")
        return

    components = schema.get("components", [])
    grouped = {}
    for component in components:
        grouped.setdefault(component.get("category", "other").replace("_", " ").title(), []).append(component.get("component", "rule").replace("_", " ").title())

    base = [
        ("Market", st.session_state.get("ai_market", "NAS100")),
        ("Timeframe", st.session_state.get("ai_timeframe", "1h")),
    ]
    items = base + [(name, ", ".join(values)) for name, values in grouped.items()]
    cols = st.columns(3)
    for index, (label, value) in enumerate(items):
        with cols[index % 3]:
            st.markdown(f'<div class="va-card"><div class="va-card-title">{label}</div><div class="va-card-value">{value}</div></div>', unsafe_allow_html=True)

    if not grouped:
        st.warning("The thesis is still too broad to produce explicit rules. Add the market context, entry trigger, confirmation and risk/exit conditions.")
    else:
        issues = strategy_contract_issues(yaml.safe_load(st.session_state.get("strategy_yaml", "")) or {})
        if issues:
            st.warning("This research contract is not ready to run yet.")
            for issue in issues:
                st.caption(f"• {issue}")
        st.markdown('<span class="va-status">Review required</span> &nbsp; <span style="color:#94a3b8;font-size:.86rem">Confirm that the interpretation matches how you actually trade.</span>', unsafe_allow_html=True)
        action, detail = st.columns([1, 2])
        with action:
            if st.button("Approve blueprint", type="primary", use_container_width=True, disabled=bool(issues)):
                st.session_state["blueprint_approved"] = True
                st.session_state["active_workspace_stage"] = "evidence"
                st.rerun()
        with detail:
            with st.expander("Advanced: inspect generated research configuration"):
                st.code(st.session_state.get("strategy_yaml", ""), language="yaml")
