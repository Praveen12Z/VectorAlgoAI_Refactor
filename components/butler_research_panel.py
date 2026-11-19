"""Dashboard entry point for the Butler MNQ exploratory backtest."""
from hashlib import sha256
import json

import pandas as pd
import streamlit as st

from core.butler_research import PAUSE_RULES, RULES, run_butler_research


def render_butler_research():
    with st.expander("MNQ five-minute reversal backtest"):
        st.caption(
            "Exploratory rule translation from Richard Butler’s Market Masters presentation. "
            "The test defines the zones, momentum, base and session mechanically."
        )
        versions = {"two_candle": "Original two-candle base", "one_candle": "One-candle pullback comparison"}
        model = st.selectbox("Base rule", tuple(versions), format_func=versions.__getitem__, key="butler_model")
        if model == "one_candle":
            st.caption("This comparison was defined after reviewing the original results. It uses the same sample.")
        for label, rule in {**RULES, "Base and entry": PAUSE_RULES[model]}.items():
            st.markdown(f"**{label}** · {rule}")
        st.caption("Upload MNQ one-minute OHLCV with UTC minute-end timestamps.")
        st.code("YYYYMMDD HHMMSS;open;high;low;close;volume", language="text")
        upload = st.file_uploader("MNQ minute-bar export", type=["txt", "csv"], key="butler_data")
        raw = upload.getvalue() if upload else None
        if st.button("Run MNQ reversal backtest", disabled=not raw, key="butler_run"):
            st.session_state.pop("butler_result", None)
            try:
                st.session_state["butler_result"] = run_butler_research(raw, pause_model=model)
            except (ValueError, TypeError, OverflowError) as exc:
                st.error(f"Could not read or test this file. {exc}")
        record = st.session_state.get("butler_result")
        if (not raw or not record or sha256(raw).hexdigest() != record["dataset_sha256"]
                or record.get("pause_model", "two_candle") != model):
            return
        st.caption(
            f"{record['coverage_start']} to {record['coverage_end']} · "
            f"{record['complete_sessions']} complete New York sessions · {record['five_minute_bars']:,} five-minute bars"
        )
        for field, label in (("excluded_incomplete_sessions", "Incomplete sessions"),
                             ("weekdays_without_rth_rows", "Weekdays without session data")):
            if record[field]:
                st.write(f"**{label}** · {', '.join(record[field])}")
        base = record["base"]
        if not base["trades"]:
            st.info("No trades executed. Performance is unassessed.")
        results = []
        for key, label in (("base", "Base cost"), ("double_cost", "Double cost")):
            sample = record[key]
            results.append({"Model": label, "Trades": len(sample["trades"]),
                            "Net P&L (USD)": sample["net_usd"] if sample["trades"] else None,
                            "Profit factor": sample["profit_factor"]})
        st.dataframe(pd.DataFrame(results), hide_index=True)
        counts = {**record["signal_counts"], **base["execution"]}
        st.dataframe(pd.DataFrame(counts.items(), columns=["Stage", "Count"]), hide_index=True)
        st.dataframe(pd.DataFrame(base["monthly_trades"].items(), columns=["Month", "Trades"]), hide_index=True)
        if record["swing_break_audit"]:
            st.markdown("**Swing breaks and base decisions**")
            st.dataframe(pd.DataFrame(record["swing_break_audit"]), hide_index=True)
        if base["trades"]:
            st.markdown("**Base-cost trade ledger**")
            ledger = pd.DataFrame(base["trades"])
            st.dataframe(ledger.drop(columns="exits"), hide_index=True)
        st.download_button("Download MNQ research evidence", json.dumps(record, indent=2),
                           file_name=f"{record['model']}-research.json", mime="application/json")
