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
    left = max(0, first - context_bars)
    right = min(len(bars) - 1, last + context_bars)
    # Keep the full series loaded so the selected trade is a zoom target.
    fig = go.Figure(go.Candlestick(
        x=bars.index, open=bars["open"], high=bars["high"],
        low=bars["low"], close=bars["close"], name="Price",
        increasing_line_color="#0f766e", decreasing_line_color="#c24156",
    ))
    spacing = bars.index.to_series().diff().dropna().min() / 2 if len(bars) > 1 else pd.Timedelta(minutes=1)
    fig.add_vrect(x0=entry - spacing, x1=exit_ + spacing,
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
            x=[timestamp], y=[price], text=[label], textposition=position,
            customdata=[timestamp.isoformat(sep=" ", timespec="minutes")], mode="markers+text", name=label,
            marker={"size": 12, "symbol": symbol, "color": color},
            hovertemplate="%{customdata}<br>%{y:,.4f}<extra>%{fullData.name}</extra>",
        )

    for field, label, color in (
        ("initial_stop", "Initial stop", "#c24156"),
        ("initial_target", "Initial target", "#0f766e"),
    ):
        price = trade.get(field)
        if pd.notna(price):
            fig.add_scatter(x=[entry - spacing, exit_ + spacing],
                            y=[price, price], mode="lines", name=label,
                            line={"color": color, "dash": "dash", "width": 1.5})

    fig.update_layout(
        height=460, dragmode="pan", hovermode="closest",
        plot_bgcolor="#fbfdff", paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#334155"},
        margin={"l": 8, "r": 10, "t": 25, "b": 15},
        xaxis={"rangeslider_visible": False, "gridcolor": "#e8eef6",
               "range": [bars.index[left] - spacing, bars.index[right] + spacing],
               "showspikes": True, "spikemode": "across", "spikesnap": "cursor"},
        yaxis={"side": "right", "title": "Price", "gridcolor": "#e8eef6"},
        legend={"orientation": "h", "y": 1.10},
    )
    return fig


def _display_timestamp(timestamp):
    stamp = pd.Timestamp(timestamp)
    if pd.isna(stamp):
        return None, "Timestamp unavailable."
    if stamp.tzinfo is None:
        return stamp.strftime("%d %b %Y · %H:%M"), "Source timezone unavailable."
    local = stamp.tz_convert("Europe/Rome")
    return local.strftime("%d %b %Y · %H:%M"), f"Italy time · Source {stamp.isoformat(sep=' ', timespec='minutes')}"


def render_trade_chart(bars, trades, key):
    if trades.empty:
        return
    st.subheader("Inspect a trade")

    def label(index):
        trade = trades.iloc[index]
        timestamp, _ = _display_timestamp(trade["entry_time"])
        return f"Trade {index + 1} · {str(trade['direction']).title()} · {timestamp or 'Time unavailable'} · P&L {trade['pnl']:+,.2f}"

    selected = st.selectbox("Jump to trade", range(len(trades)), format_func=label,
                            key=f"{key}_selected_trade")
    trade = trades.iloc[selected]
    outcome = trade["pnl"]
    st.caption(f"{str(trade['direction']).title()} trade · Net P&L {outcome:+,.2f}")
    for column, title, field, timestamp_field in zip(
        st.columns(3),
        ("Signal candle time", "Entry time", "Exit candle time"),
        (None, "entry_price", "exit_price"),
        ("signal_time", "entry_time", "exit_time"),
    ):
        timestamp, source = _display_timestamp(trade.get(timestamp_field))
        column.metric(title, timestamp or "Unavailable")
        column.caption(source)
        if field and pd.notna(trade.get(field)):
            column.write(f"Fill price **{trade[field]:,.4f}**")
        elif not field and timestamp:
            column.caption("Signal evaluated at candle close.")

    if bars is None or bars.empty:
        st.info("This saved record includes execution times and prices. Rerun the backtest to inspect its candles.")
        return
    try:
        figure = build_trade_chart(bars, trade)
    except ValueError as exc:
        st.warning(str(exc))
        return
    st.plotly_chart(figure, use_container_width=True, key=f"{key}_trade_chart_{selected}",
                    config={"scrollZoom": True, "displaylogo": False})
    if pd.notna(reason := trade.get("exit_reason")):
        description = {"TP": "Target hit", "SL": "Stop hit", "TIME": "Time exit"}.get(str(reason), str(reason))
        st.caption(f"Exit reason: {description}")
    st.caption("Drag to pan through the run or scroll to zoom. Select another trade to jump to it. Fill markers show the backtest price and candle.")
