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
        st.info("Use Strategy Brief and Rule Blueprint to define the research contract, then continue to Backtest Results.")


def _render_thesis_editor():
    st.markdown('<div class="va-page-kicker">Strategy Brief</div><div class="va-title">Turn your trading idea into testable rules</div><div class="va-subtitle">Describe the edge as you trade it. VectorAlgoAI will expose every assumption before testing.</div>', unsafe_allow_html=True)
    editor, context = st.columns([1.55, .7], gap="medium")
    with editor:
        st.markdown('<div class="va-composer"><div class="va-composer-head"><span class="va-ai-orb">✦</span><div><div class="va-panel-title">Describe your strategy</div><div class="va-panel-copy">Use plain English. Include setup, confirmation, risk and exit when possible.</div></div></div></div>', unsafe_allow_html=True)
        strategy_text = st.text_area(
            "Strategy idea",
            height=230,
            key="ai_text",
            placeholder="Example: Trade NAS100 long when price retests a confirmed 1H support zone after a breakout. Require a bullish rejection candle on 5m. Avoid high-impact news. Risk 0.5% and target 2R."
        )
    with context:
        st.markdown('<div class="va-card"><div class="va-panel-title">Research setup</div><div class="va-panel-copy">Applied to the first evidence run</div><div style="height:.8rem"></div>', unsafe_allow_html=True)
        market = st.selectbox("Market", ["NAS100", "XAUUSD", "US30", "BTCUSD", "ETHUSD"], key="ai_market")
        timeframe = st.selectbox("Primary timeframe", ["15m", "1h", "4h", "1d"], index=1, key="ai_timeframe")
        st.markdown('<div class="va-chip">✓ Realistic costs</div><div class="va-chip">✓ Hold-out validation</div><div class="va-panel-copy" style="margin-top:.9rem">Research-safe by default. Results stay separate from future validation.</div></div>', unsafe_allow_html=True)

    if st.button(
        "Build Rule Blueprint  →", use_container_width=True, type="primary"
    ):

        if not strategy_text.strip():
            st.warning("Please enter a strategy.")
            return

        schema = build_strategy_from_text(
            strategy_text
        )

        generated_yaml = _compile_blueprint(schema, market, timeframe)

        # Keep the generated contract separate from the editable Evidence widget.
        # This prevents a stale/blank Streamlit widget value from replacing a new
        # Blueprint between the Thesis and Evidence stages.
        st.session_state["blueprint_yaml"] = generated_yaml
        st.session_state["strategy_yaml"] = generated_yaml
        st.session_state.pop("evidence_yaml_editor", None)
        st.session_state.pop("approved_strategy_yaml", None)
        st.session_state["blueprint_schema"] = schema
        st.session_state["blueprint_approved"] = False
        st.session_state["active_workspace_stage"] = "blueprint"
        st.rerun()


def _render_blueprint():
    st.markdown('<div class="va-page-kicker">Rule Blueprint</div><div class="va-title">Confirm exactly what the AI will test</div><div class="va-subtitle">Human-readable logic and machine rules stay synchronized.</div>', unsafe_allow_html=True)
    schema = st.session_state.get("blueprint_schema")
    if not schema:
        st.info("There is no Rule Blueprint yet. Start by describing the strategy in Strategy Brief.")
        return

    # Repair research sessions created before Blueprint YAML was persisted. The
    # schema is the source of truth at this stage, so a blank YAML value must
    # never be displayed or approved.
    generated_yaml = st.session_state.get("blueprint_yaml")
    if not isinstance(generated_yaml, str) or not generated_yaml.strip():
        generated_yaml = _compile_blueprint(
            schema,
            st.session_state.get("ai_market", "NAS100"),
            st.session_state.get("ai_timeframe", "1h"),
        )
        st.session_state["blueprint_yaml"] = generated_yaml

    current_yaml = st.session_state.get("strategy_yaml")
    if not isinstance(current_yaml, str) or not current_yaml.strip():
        st.session_state["strategy_yaml"] = generated_yaml
        current_yaml = generated_yaml

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
        try:
            parsed_yaml = yaml.safe_load(current_yaml) or {}
            issues = strategy_contract_issues(parsed_yaml)
        except yaml.YAMLError as exc:
            issues = [f"Generated Blueprint YAML is invalid: {exc}"]

        if issues:
            st.warning("This research contract is not ready to run yet.")
            for issue in issues:
                st.caption(f"• {issue}")

        st.markdown('<span class="va-status">Review required</span> &nbsp; <span style="color:#94a3b8;font-size:.86rem">Confirm that the interpretation matches how you actually trade.</span>', unsafe_allow_html=True)
        action, detail = st.columns([1, 2])
        with action:
            if st.button("Approve & Run Backtest  →", type="primary", use_container_width=True, disabled=bool(issues)):
                # Freeze the reviewed contract. Evidence must consume this exact
                # value instead of relying on a widget-backed session key.
                st.session_state["blueprint_yaml"] = current_yaml
                st.session_state["approved_strategy_yaml"] = current_yaml
                st.session_state["strategy_yaml"] = current_yaml
                st.session_state.pop("evidence_yaml_editor", None)
                st.session_state["blueprint_approved"] = True
                st.session_state["active_workspace_stage"] = "evidence"
                st.rerun()
        with detail:
            with st.expander("Machine contract · generated YAML"):
                st.code(current_yaml, language="yaml")


def _compile_blueprint(schema: dict, market: str, timeframe: str) -> str:
    """Compile and verify the non-empty YAML required by the research workflow."""
    generated_yaml = compile_schema_to_yaml(schema, market=market, timeframe=timeframe)
    if not isinstance(generated_yaml, str) or not generated_yaml.strip():
        raise ValueError("The Blueprint compiler did not produce machine-readable YAML.")
    return generated_yaml
