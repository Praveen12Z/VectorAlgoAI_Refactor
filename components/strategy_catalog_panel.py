"""Starter specifications are separate from a user's saved evidence."""
import json
import streamlit as st
import pandas as pd
from io import BytesIO
from components.strategy_explainers import GUIDES, render_strategy_example
from core.orb_research import screen_opening_range, selection_record
from core.strategy_catalog import CATALOG, COMMON_PROTOCOL, catalog_export, load_template


PAPER_REFERENCES = {
    "PR-001": {
        "title": "Time Series Momentum",
        "citation": "Tobias J. Moskowitz, Yao Hua Ooi, and Lasse Heje Pedersen · Journal of Financial Economics 104(2), 228–250 · 2012",
        "link": "https://doi.org/10.1016/j.jfineco.2011.11.003",
        "finding": (
            "The authors examined 58 futures and forward instruments across several asset classes. "
            "They found that past returns could persist for up to a year and that the effect "
            "partly reversed over longer horizons."
        ),
    },
    "PR-002": {
        "title": "A Profitable Day Trading Strategy for the U.S. Equity Market",
        "citation": "Carlo Zarattini, Andrea Barbon, and Andrew Aziz · Swiss Finance Institute Research Paper 24-98 · 2024",
        "link": "https://www.sfi.ch/en/publications/n-24-98-a-profitable-day-trading-strategy-for-the-u.s.-equity-market",
        "finding": (
            "The authors studied five-minute opening-range breakouts across US stocks from 2016 to 2023. "
            "They reported better historical results when they focused on stocks with unusually "
            "high opening activity."
        ),
    },
}


def render_strategy_catalog():
    starters = {item["id"]: item for item in CATALOG}
    mode = st.radio("Show", ("All strategies", "Ready to backtest", "Research only"),
                    horizontal=True)
    choices = [
        key for key, item in starters.items()
        if mode == "All strategies"
        or (mode == "Ready to backtest" and not item["implementation_gaps"])
        or (mode == "Research only" and item["implementation_gaps"])
    ]
    if not choices:
        st.info("No strategies in this view.")
        return
    selected = st.selectbox("Choose a strategy", choices,
                            format_func=lambda key: f"{key} · {starters[key]['name']}")
    item = starters[selected]
    with st.container(border=True):
        st.subheader(item["name"])
        st.caption(f"{item['id']} · v{item['version']} · {item['family']} · {item['market']} · {item['timeframe']}")
        description, steps, example = GUIDES[item["id"]]
        st.write(description)
        render_strategy_example(item["id"], example, steps)
        if item["implementation_gaps"]:
            st.info(item["status"])
        else:
            st.success("Ready to backtest")
        if st.button("Open as new research draft", key=f"load_{item['id']}", type="primary"):
            load_template(st.session_state, item)
            st.rerun()
        st.caption("Opening a strategy replaces the current unsaved draft and session result.")
    with st.expander("Research notes and references"):
        paper = PAPER_REFERENCES.get(item["id"])
        if paper:
            st.subheader(paper["title"])
            st.caption(paper["citation"])
            st.markdown("**What the authors found**")
            st.write(paper["finding"])
            st.markdown("**VectorAlgoAI research status**")
            st.write(item["source_concept"])
        else:
            st.markdown("**Research basis**")
            st.write(item["source_concept"])
            st.caption("This catalog entry is a VectorAlgoAI adaptation. Its reference explains the underlying concept.")
        st.markdown("**How VectorAlgoAI defines the setup**")
        st.write(item["refinements"])
        url = paper["link"] if paper else item["source_url"]
        text = "Publication record" if paper else "Concept reference"
        st.caption(f"Reviewed {item['reviewed_on']}")
        st.markdown(f"[{text}]({url})")

    with st.expander("Exact rules and limitations"):
        st.markdown("**Proposed rules**")
        for rule in item['rules']:
            st.write(f"• {rule}")
        st.markdown("**Where it can fail**")
        st.write(item['failure_modes'])
        if item['implementation_gaps']:
            st.warning("Automated testing blocked: " + "; ".join(item['implementation_gaps']) + ".")
        st.markdown("**Research and execution protocol**")
        st.write(item.get("research_protocol", COMMON_PROTOCOL))

    st.download_button("Download research specification", json.dumps(catalog_export(item), indent=2),
        file_name=f"{item['id']}-v{item['version']}.json", mime="application/json")


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
