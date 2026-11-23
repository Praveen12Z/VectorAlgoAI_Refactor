"""Market and cadence entry point for the intraday strategy tester."""

from hashlib import sha256
from dataclasses import replace
import json

import pandas as pd
import streamlit as st

from core.intraday_tester import (
    EMA_RECLAIM_HOLD_PRESETS, STARTERS, STARTER_MARKETS, run_intraday_tester, starter_label,
)


def render_intraday_tester():
    st.subheader("Strategy Tester")
    requested = st.session_state.pop("open_intraday_starter", None)
    if requested is not None:
        st.session_state["intraday_market"] = requested.market
        st.session_state[f"intraday_strategy_{requested.market}"] = requested
    market = st.radio("Market", STARTER_MARKETS,
                      horizontal=True, key="intraday_market")
    choices = [starter for starter in STARTERS if starter.market == market]
    starter = st.selectbox(
        "Strategy", choices, key=f"intraday_strategy_{market}",
        format_func=starter_label,
    )
    if starter.id == "FUT-01":
        hold = st.radio(
            "EMA Reclaim version", tuple(EMA_RECLAIM_HOLD_PRESETS), index=1,
            format_func=EMA_RECLAIM_HOLD_PRESETS.__getitem__, horizontal=True,
            key="intraday_ema_reclaim_hold",
        )
        starter = replace(starter, hold=hold)
        st.caption(
            "The tuned version changes the time exit only. Its 40-minute hold was selected on the "
            "existing MNQ sample. Use a different period to validate it."
        )
    floor, ceiling = starter.target
    st.caption(
        f"Research starter · {starter.timeframe}m signals · Long and short · "
        f"Target {floor}–{ceiling} trades per {starter.cadence}"
    )
    with st.expander("Rules and required data"):
        trigger = (
            f"Enter in the direction of a close crossing the {starter.period}-bar EMA."
            if starter.rule == "EMA reclaim" else
            f"Enter in the direction of a close beyond the prior {starter.period}-bar high or low."
        )
        st.write(
            f"{trigger} Indicators reset each session. Use the next minute open and one position at a time. "
            f"The stop is the mean true range of the last 8 signal bars, and the target is 1.5 times "
            f"the stop distance before any tick rounding. Exit after {starter.hold} minutes or at 16:00 New York "
            "if neither level has filled. Protective fills use minute bars, with the stop taking priority "
            "when both levels are touched."
        )
        st.write(
            "Use complete 09:30–16:00 New York sessions. Upload one broker instrument or dated futures "
            "contract per file. Enter the all-in round-trip cost for one unit in USD. For broker candles, "
            "account for the bar's quote basis when estimating spread and slippage."
        )
    symbol = None
    point_value = starter.point_value
    if point_value is None:
        st.caption("Broker CSV · Minute starts with timezone · timestamp, open, high, low, close")
        point_value = st.number_input("USD per price point for one broker unit", min_value=0.0,
                                      value=0.0, format="%.6f", key=f"intraday_point_{starter.id}")
    else:
        source = st.selectbox("Data format", ("UTC minute-end text", "Databento OHLCV CSV"),
                              key=f"intraday_data_{starter.id}")
        st.caption(f"One contract · USD {point_value:g} per point · Tick {starter.tick:g}")
        if source == "Databento OHLCV CSV":
            symbol = st.text_input("Dated raw contract symbol", key=f"intraday_symbol_{starter.id}").strip().upper()
        else:
            st.caption("Text format · YYYYMMDD HHMMSS;open;high;low;close;volume")
    raw_file = st.file_uploader(f"{starter.symbol} minute bars", type=["csv", "txt"],
                                key=f"intraday_upload_{starter.id}")
    cost = st.number_input("All-in cost per round trip (USD)", min_value=0.0, value=0.0,
                           step=0.1, key=f"intraday_cost_{starter.id}")
    raw = raw_file.getvalue() if raw_file else None
    signature = (starter, sha256(raw).hexdigest(), cost, point_value, symbol) if raw else None
    if st.button("Run strategy test", type="primary",
                 disabled=not (raw and cost > 0 and point_value > 0 and symbol != "")):
        st.session_state.pop("intraday_tester_result", None)
        try:
            result = run_intraday_tester(raw, starter, round_turn_cost=cost,
                                         cfd_point_value=point_value, raw_symbol=symbol)
        except (ValueError, TypeError, OverflowError) as exc:
            st.error(str(exc))
        else:
            st.session_state["intraday_tester_result"] = (signature, result)
    saved = st.session_state.get("intraday_tester_result")
    if not saved or saved[0] != signature:
        return

    result = saved[1]
    st.caption(result["parameter_selection"])
    median, target_metric, base, stress = st.columns(4)
    observed = result["median_trades"]
    median.metric(f"Median trades / {starter.cadence}", f"{observed:g}" if observed is not None else "—")
    rate = result["at_least_floor_pct"]
    target_metric.metric(f"Reached {floor}+ trades", f"{rate:.0f}%" if rate is not None else "—")
    base.metric("Net at base costs", f"${result['base_net']:,.2f}")
    stress.metric("Net at double costs", f"${result['double_cost_net']:,.2f}")
    band = result["in_band_pct"]
    within = f" · {band:.0f}% of periods within {floor}–{ceiling}" if band is not None else ""
    st.write(f"**Cadence: {result['cadence_status']}** · {result['periods']} measured periods · "
             f"{len(result['trades'])} completed trades{within}")
    st.caption(
        "Cadence is measured on complete sessions or weeks with five complete sessions, including zero-trade periods. "
        "The screening status requires 20 sessions or four weeks. P&L covers all included sessions."
    )
    activity, trades = st.tabs(["Trade frequency", "Trade ledger"])
    with activity:
        activity_frame = pd.DataFrame(result["days" if starter.cadence == "day" else "weeks"])
        st.dataframe(activity_frame.rename(columns={
            "base_net": "Net at base costs (USD)", "double_cost_net": "Net at double costs (USD)",
        }), hide_index=True)
        for key, label in (("incomplete_sessions", "Incomplete sessions"), ("weekdays_without_bars", "Weekdays without bars")):
            if result[key]:
                st.caption(f"{label} · {', '.join(result[key])}")
    with trades:
        if result["trades"]:
            st.dataframe(pd.DataFrame(result["trades"]), hide_index=True)
        else:
            st.info("No trades on the supplied sample.")
    file_stem = f"{starter.id}-{starter.hold}m-hold" if starter.id == "FUT-01" else starter.id
    st.download_button("Download test results", json.dumps(result, indent=2),
                       file_name=f"{file_stem}-intraday-test.json", mime="application/json")
