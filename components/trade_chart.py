"""Zoomed candle view for verifying individual simulated trades."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def build_trade_chart(bars, trade, context_bars=12):
    """Plot exact execution candles and recorded prices without approximating missing bars."""
    entry = pd.Timestamp(trade["entry_time"])
    exit_ = pd.Timestamp(trade["exit_time"])
    signal = pd.Timestamp(trade.get("signal_time"))
    anchors = [entry, exit_]
    if pd.notna(signal):
        anchors.insert(0, signal)
    if any(timestamp not in bars.index for timestamp in anchors):
        raise ValueError("One or more trade candles are missing from this run's price data.")

    first = bars.index.get_loc(min(anchors))
    last = bars.index.get_loc(max(anchors))
    window = bars.iloc[max(0, first - context_bars):last + context_bars + 1]
    # Sequential bar numbers compress weekends and session gaps while hover
    # labels and event details retain the original bar timestamps.
    positions = {timestamp: i for i, timestamp in enumerate(window.index)}
    timestamps = [timestamp.isoformat(sep=" ", timespec="minutes") for timestamp in window.index]
    fig = go.Figure(go.Candlestick(
        x=list(range(len(window))), open=window["open"], high=window["high"],
        low=window["low"], close=window["close"], text=timestamps, name="Price",
        increasing_line_color="#0f766e", decreasing_line_color="#c24156",
    ))
    fig.add_vrect(x0=positions[entry] - 0.45, x1=positions[exit_] + 0.45,
                  fillcolor="#dbeafe", opacity=0.5, line_width=0, layer="below")

    markers = [
        ("Entry fill", entry, trade["entry_price"], "#1d4ed8",
         "triangle-down" if trade.get("direction") == "short" else "triangle-up", "top center"),
        ("Exit fill", exit_, trade["exit_price"], "#9333ea", "x", "bottom center"),
    ]
    if pd.notna(signal):
        markers.insert(0, ("Signal close", signal, bars.at[signal, "close"],
                           "#b45309", "diamond", "top left"))
    for label, timestamp, price, color, symbol, position in markers:
        fig.add_scatter(
            x=[positions[timestamp]], y=[price], text=[label], textposition=position,
            customdata=[timestamps[positions[timestamp]]], mode="markers+text", name=label,
            marker={"size": 12, "symbol": symbol, "color": color},
            hovertemplate="%{customdata}<br>%{y:,.4f}<extra>%{fullData.name}</extra>",
        )

    for field, label, color in (
        ("initial_stop", "Initial stop", "#c24156"),
        ("initial_target", "Initial target", "#0f766e"),
    ):
        price = trade.get(field)
        if pd.notna(price):
            fig.add_scatter(x=[positions[entry] - 0.45, positions[exit_] + 0.45],
                            y=[price, price], mode="lines", name=label,
                            line={"color": color, "dash": "dash", "width": 1.5})

    tick_indices = sorted(set(range(0, len(window), max(1, len(window) // 6))) |
                          {positions[entry], positions[exit_]})
    fig.update_layout(
        height=440, dragmode="pan", hovermode="closest",
        margin={"l": 8, "r": 10, "t": 25, "b": 15},
        xaxis={"rangeslider_visible": False, "tickvals": tick_indices,
               "ticktext": [window.index[i].strftime("%d %b %H:%M") for i in tick_indices]},
        yaxis={"side": "right", "title": "Price"},
        legend={"orientation": "h", "y": 1.10},
    )
    return fig


def render_trade_chart(bars, trades, key):
    if trades.empty:
        return
    st.subheader("Inspect a trade")
    if bars is None or bars.empty:
        st.info("Candle inspection is available from the current backtest. Saved trade records contain fills but do not store price candles.")
        return

    def label(index):
        trade = trades.iloc[index]
        timestamp = pd.Timestamp(trade["entry_time"])
        return f"Trade {index + 1} · {str(trade['direction']).title()} · {timestamp:%d %b %Y %H:%M} · P&L {trade['pnl']:+,.2f}"

    selected = st.selectbox("Trade to inspect", range(len(trades)), format_func=label,
                            key=f"{key}_selected_trade")
    trade = trades.iloc[selected]
    try:
        figure = build_trade_chart(bars, trade)
    except ValueError as exc:
        st.warning(str(exc))
        return

    for column, title, field, timestamp_field in zip(
        st.columns(3),
        ("Signal candle", "Entry fill", "Exit fill"),
        (None, "entry_price", "exit_price"),
        ("signal_time", "entry_time", "exit_time"),
    ):
        timestamp = trade.get(timestamp_field)
        value = f"{trade[field]:,.4f}" if field else "Completed close"
        if pd.isna(timestamp):
            value = "Unavailable"
        column.metric(title, value)
        if pd.notna(timestamp):
            column.caption(pd.Timestamp(timestamp).isoformat(sep=" ", timespec="minutes"))
    st.plotly_chart(figure, use_container_width=True, key=f"{key}_trade_chart_{selected}",
                    config={"scrollZoom": True, "displaylogo": False})
    if pd.notna(reason := trade.get("exit_reason")):
        description = {"TP": "Target hit", "SL": "Stop hit", "TIME": "Time exit"}.get(str(reason), str(reason))
        st.caption(f"Exit reason: {description}")
    st.caption("Shading shows the bars while the position was open. Entry and exit timestamps identify the simulation candles. OHLC bars do not show the exact intrabar fill time.")
