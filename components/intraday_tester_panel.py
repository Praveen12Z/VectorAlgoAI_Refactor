"""Market and cadence entry point for the intraday strategy tester."""

from dataclasses import replace
from datetime import timedelta
from hashlib import sha256
import json
import os

import pandas as pd
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError

from core.databento_history import fetch_futures_minutes
from core.intraday_tester import (
    EMA_RECLAIM_ID, STARTERS, STARTER_MARKETS, run_intraday_tester, starter_label,
)


def _databento_key():
    if key := os.getenv("DATABENTO_API_KEY"):
        return key
    try:
        return st.secrets.get("DATABENTO_API_KEY")
    except StreamlitSecretNotFoundError:
        return None


def render_dashboard_ema_reclaim():
    baseline = next(starter for starter in STARTERS if starter.id == EMA_RECLAIM_ID)
    tuned = replace(baseline, hold=40, reward_multiple=1.0)
    with st.container(border=True):
        st.subheader("MNQ EMA Reclaim")
        st.caption("40-minute max hold · 1R target · One MNQ contract")
        _render_intraday_run(tuned, key_prefix="dashboard_ema_reclaim", default_cost=2.60)


def render_intraday_tester():
    st.subheader("Strategy Tester")
    requested = st.session_state.pop("open_intraday_starter", None)
    if requested is not None and requested.id != EMA_RECLAIM_ID:
        st.session_state["intraday_market"] = requested.market
        st.session_state[f"intraday_strategy_{requested.market}"] = requested
    market = st.radio("Market", STARTER_MARKETS,
                      horizontal=True, key="intraday_market")
    choices = [starter for starter in STARTERS if starter.market == market and starter.id != EMA_RECLAIM_ID]
    starter = st.selectbox(
        "Strategy", choices, key=f"intraday_strategy_{market}",
        format_func=starter_label,
    )
    _render_intraday_run(starter, key_prefix="intraday")


def _render_intraday_run(starter, *, key_prefix, default_cost=0.0):
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
            f"The stop is the mean true range of the last 8 signal bars, and the target is {starter.reward_multiple:g} times "
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
    request_dates = None
    api_key = None
    if point_value is None:
        st.caption("Broker CSV · Minute starts with timezone · timestamp, open, high, low, close")
        st.caption("These execution tests use the broker's instrument prices. Yahoo data is available in the standard research workflow.")
        point_value = st.number_input("USD per price point for one broker unit", min_value=0.0,
                                      value=0.0, format="%.6f", key=f"{key_prefix}_point_{starter.id}")
    else:
        api_key = _databento_key()
        sources = ["UTC minute-end text", "Databento OHLCV CSV"]
        if api_key:
            sources.insert(0, "Load historical bars from Databento")
        else:
            st.caption("Automatic futures history becomes available when Databento is configured.")
        source = st.selectbox("Market data", sources,
                              key=f"{key_prefix}_data_{starter.id}")
        st.caption(f"One contract · USD {point_value:g} per point · Tick {starter.tick:g}")
        if source != "UTC minute-end text":
            symbol = st.text_input("Dated raw contract symbol", key=f"{key_prefix}_symbol_{starter.id}").strip().upper()
            if source == "Load historical bars from Databento":
                yesterday = pd.Timestamp.now(tz="America/New_York").date() - timedelta(days=1)
                request_dates = st.date_input(
                    "Backtest dates (New York)", value=(yesterday - timedelta(days=29), yesterday),
                    max_value=yesterday, key=f"{key_prefix}_dates_{starter.id}",
                )
                st.caption("One contract and up to 31 days per request. Databento usage charges may apply.")
        else:
            st.caption("Text format · YYYYMMDD HHMMSS;open;high;low;close;volume")
    raw = None
    if request_dates is None:
        raw_file = st.file_uploader(f"{starter.symbol} minute bars", type=["csv", "txt"],
                                    key=f"{key_prefix}_upload_{starter.id}")
        raw = raw_file.getvalue() if raw_file else None
    cost = st.number_input("All-in cost per round trip (USD)", min_value=0.0, value=default_cost,
                           step=0.1, key=f"{key_prefix}_cost_{starter.id}")
    data_selection = request_dates if request_dates is not None else sha256(raw).hexdigest() if raw else None
    ready = len(request_dates) == 2 if request_dates is not None else bool(raw)
    ready = ready and symbol != ""
    signature = (starter, data_selection, cost, point_value, symbol)
    result_key = f"{key_prefix}_tester_result"
    if st.button("Run EMA Reclaim" if starter.id == EMA_RECLAIM_ID else "Run strategy test", type="primary",
                 disabled=not (ready and cost > 0 and point_value > 0)):
        st.session_state.pop(result_key, None)
        try:
            if request_dates is not None:
                with st.spinner("Loading historical futures bars…"):
                    raw = fetch_futures_minutes(api_key, starter.symbol, symbol, *request_dates)
            result = run_intraday_tester(raw, starter, round_turn_cost=cost,
                                         cfd_point_value=point_value, raw_symbol=symbol)
        except (ValueError, TypeError, OverflowError) as exc:
            st.error(str(exc))
        else:
            if request_dates is not None:
                result["data_source"] = {
                    "provider": "Databento", "dataset": "GLBX.MDP3", "schema": "ohlcv-1m",
                    "start_date_ny": request_dates[0].isoformat(), "end_date_ny": request_dates[1].isoformat(),
                }
            st.session_state[result_key] = (signature, result)
    saved = st.session_state.get(result_key)
    if not saved:
        return

    result = saved[1]
    if saved[0] != signature:
        if key_prefix != "dashboard_ema_reclaim" or ready or saved[0][0] != starter:
            return
        st.caption(f"Last completed run · ${result['round_turn_cost']:.2f} per modeled round trip")
    st.caption(result["parameter_selection"])
    median, target_metric, base, stress = st.columns(4)
    observed = result["median_trades"]
    median.metric(f"Median trades / {starter.cadence}", f"{observed:g}" if observed is not None else "—")
    rate = result["at_least_floor_pct"]
    target_metric.metric(f"Reached {floor}+ trades", f"{rate:.0f}%" if rate is not None else "—")
    base.metric("Net at base costs", f"${result['base_net']:,.2f}")
    stress.metric("Net at double costs", f"${result['double_cost_net']:,.2f}")
    profit_factor, win_rate, drawdown = st.columns(3)
    pf = result.get("profit_factor")
    wins = result.get("win_rate_pct")
    dd = result.get("max_closed_trade_drawdown_usd")
    profit_factor.metric("Profit factor", f"{pf:.2f}" if pf is not None else "—")
    win_rate.metric("Win rate", f"{wins:.1f}%" if wins is not None else "—")
    drawdown.metric("Closed-trade drawdown", f"${dd:,.2f}" if dd is not None else "—")
    band = result["in_band_pct"]
    within = f" · {band:.0f}% of periods within {floor}–{ceiling}" if band is not None else ""
    st.write(f"**Cadence: {result['cadence_status']}** · {result['periods']} measured periods · "
             f"{len(result['trades'])} completed trades{within}")
    if starter.id == EMA_RECLAIM_ID:
        goal = result["daily_profit_target_usd"]
        average = result["average_daily_base_net"]
        gap = average - goal
        daily_base, daily_stress, target_days = st.columns(3)
        daily_base.metric("Average net per session", f"${average:,.2f}",
                          delta=f"{gap:+,.2f} USD vs goal of ${goal:g}")
        daily_stress.metric("Average net per session at double costs",
                            f"${result['average_daily_double_cost_net']:,.2f}")
        target_days.metric(f"Sessions earning ${goal:g} or more",
                           f"{result['sessions_at_daily_target']} / {result['periods']}")
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
    file_stem = (
        f"{starter.id}-{starter.hold}m-hold-{starter.reward_multiple:g}R"
        if starter.id == EMA_RECLAIM_ID else starter.id
    )
    st.download_button("Download test results", json.dumps(result, indent=2),
                       file_name=f"{file_stem}-intraday-test.json", mime="application/json")
