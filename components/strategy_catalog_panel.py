"""Starter specifications are separate from a user's saved evidence."""
import json
import streamlit as st
import pandas as pd
from io import BytesIO
from components.experiment_library_panel import label, render_saved_evidence
from core.auth import AccessServiceError
from core.orb_research import screen_opening_range, selection_record
from core.strategy_catalog import CATALOG, COMMON_PROTOCOL, catalog_export, load_template


def render_strategy_catalog(records, load_record, evidence_available):
    st.subheader("Sourced strategy starters")
    st.caption(f"{len(CATALOG)} research specifications · implementation status shown separately · none validated")
    st.write("Refined means the rules are more explicit, not that returns have improved. Sources explain the underlying concepts; VectorAlgoAI's thresholds and risk rules are research adaptations.")
    selected = st.selectbox("Choose a strategy", [x['id'] for x in CATALOG],
        format_func=lambda id: next(f"{x['id']} · {x['name']}" for x in CATALOG if x['id'] == id))
    item = next(x for x in CATALOG if x['id'] == selected)
    st.markdown(f"**{item['name']} · v{item['version']}**")
    st.caption(f"{item['family']} · Proposed market: {item['market']} · {item['timeframe']}")
    st.info(item['status'])
    if st.button("Open as new research draft", key=f"load_{item['id']}", type="primary"):
        load_template(st.session_state, item)
        st.rerun()
    st.caption("Opening a strategy replaces the current unsaved draft and session result.")
    render_catalog_evidence(item, records, load_record, evidence_available)
    st.markdown(f"[Read original concept]({item['source_url']}) · Reviewed {item['reviewed_on']}")
    st.write(item['source_concept'])
    st.markdown("**Proposed rules**")
    for rule in item['rules']:
        st.write(f"• {rule}")
    st.markdown("**What we refined**")
    st.write(item['refinements'])
    st.markdown("**Where it can fail**")
    st.write(item['failure_modes'])
    if item['implementation_gaps']:
        st.warning("Automated testing blocked: " + "; ".join(item['implementation_gaps']) + ".")
    with st.expander("Shared research and execution protocol"):
        st.write(item.get('research_protocol', COMMON_PROTOCOL))
        st.caption("Execution readiness is specific to each research track. A working selector does not imply a working backtest.")
    st.download_button("Download research specification", json.dumps(catalog_export(item), indent=2),
        file_name=f"{item['id']}-v{item['version']}.json", mime="application/json")
    if item['id'] == 'PR-002':
        render_orb_selection()


def render_catalog_evidence(item, records, load_record, evidence_available):
    matches = {}
    for record in records:
        origin = (record.get("execution_assumptions") or {}).get("catalog_origin") or {}
        if origin.get("id") == item["id"] and origin.get("version") == item["version"]:
            matches[record["record_hash"]] = record
    if matches:
        with st.expander("View results and trades", expanded=True):
            selected = st.selectbox(
                "Choose a backtest or review", list(matches),
                format_func=lambda record_hash: label(matches[record_hash]),
                key=f"catalog_evidence_{item['id']}",
            )
            try:
                render_saved_evidence(load_record(selected), key=f"catalog_{item['id']}")
            except AccessServiceError:
                st.error("Could not load the saved evidence. Please retry.")
    elif item["id"] == "PR-001":
        st.info("The linked paper reports the authors' results. VectorAlgoAI replication is pending, so there is no VectorAlgoAI backtest or trade ledger for this strategy.")
    elif item["id"] == "PR-002":
        st.info("The screener below shows qualifying stock candidates. Backtest results and a trade ledger require implementing order execution.")
    elif item["implementation_gaps"]:
        st.info("Backtest results will be available once this strategy's rules can run in the backtester.")
    elif evidence_available:
        st.info("No matching run in your recent saved research. Open this starter as a draft, approve the rules, and run a backtest to generate results and trades.")
    else:
        st.warning("Saved backtests could not be checked. You can still open this starter as a research draft.")


def render_orb_selection():
    st.subheader("Opening-volume research screener")
    st.write("Upload US-stock daily history and completed 09:30–09:35 New York opening bars. This selects research candidates; it does not simulate trades or assess profitability.")
    st.code("session,symbol,open,high,low,close,volume\n2026-01-02,EXAMPLE,10,11,9,10.5,2000000", language="text")
    st.caption("Format example only, not market data. Dates use YYYY-MM-DD; prices are USD and volume is shares. Include at least 15 prior daily sessions and 14 prior opening bars per stock. Use consistent corporate-action treatment. Missing supplied-session history is rejected. A complete exchange calendar and survivorship-safe universe are not verified here.")
    daily = st.file_uploader("Daily history CSV", type=['csv'], key='orb_daily')
    opening = st.file_uploader("Completed five-minute opening bars CSV", type=['csv'], key='orb_opening')
    confirmed = st.checkbox("I confirm these are US-stock opening bars from 09:30–09:35 America/New_York, with matching daily history.", key='orb_input_confirm')
    if st.button("Screen research candidates", disabled=not (daily and opening and confirmed), key='orb_screen'):
        try:
            db, ob = daily.getvalue(), opening.getvalue()
            if max(len(db), len(ob)) > 10_000_000:
                raise ValueError("Use CSV files smaller than 10 MB for this initial screener.")
            d, o = pd.read_csv(BytesIO(db)), pd.read_csv(BytesIO(ob))
            if len(o) > 10000 or len(d) > 100000:
                raise ValueError("Initial research limit: 10,000 opening rows and 100,000 daily rows. Use a smaller research sample.")
            result = screen_opening_range(d, o)
            record = selection_record(db, ob, result)
            st.session_state['orb_screen_result'] = (record, result)
        except (ValueError, KeyError, TypeError) as exc:
            st.session_state.pop('orb_screen_result', None)
            st.error(str(exc))
    saved = st.session_state.get('orb_screen_result')
    if saved:
        record, result = saved
        from hashlib import sha256
        matches = (daily is not None and opening is not None
                   and sha256(daily.getvalue()).hexdigest() == record['daily_sha256']
                   and sha256(opening.getvalue()).hexdigest() == record['opening_sha256'])
        if not matches or not confirmed:
            st.info("Inputs changed. Screen again to display results for these files.")
            return
        st.write(f"{int(result.selected.sum())} selected symbol/session candidates; these are not trade counts.")
        st.dataframe(result, hide_index=True, use_container_width=True)
        st.download_button("Download candidate audit CSV", result.to_csv(index=False), 'orb-candidates.csv', 'text/csv')
        st.download_button("Download reproducible selection record", json.dumps(record, indent=2),
                           'orb-selection-record.json', 'application/json')
        st.caption("The record contains input hashes, model version, assumptions and all selection results. Retain both input CSVs to reproduce it. This screener record is downloadable; database storage is not yet connected.")
