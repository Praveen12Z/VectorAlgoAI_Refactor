"""Zoomed candle view for verifying individual simulated trades."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def build_trade_chart(bars, trade, context_bars=30, *, full_run=False, center="Entry"):
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
    entry_bar = bars.index.get_loc(entry)
    exit_bar = bars.index.get_loc(exit_)
    signal_bar = bars.index.get_loc(signal) if pd.notna(signal) else None
    if full_run:
        left, right = 0, len(bars) - 1
    elif exit_bar - entry_bar > 30 or right - left + 1 > 100:
        anchor = entry_bar if center == "Entry" else exit_bar
        left = max(0, anchor - 42)
        right = min(len(bars) - 1, left + 84)
    visible = bars.iloc[left:right + 1]

    def display_time(stamp):
        if stamp.tzinfo is not None:
            stamp = stamp.tz_convert("Europe/Rome")
        return stamp.strftime("%d %b %Y · %H:%M %Z").strip()

    prices = []
    if full_run:
        fig = go.Figure(go.Scatter(
            x=list(range(len(bars))), y=bars["close"], mode="lines",
            name="Close", showlegend=False, line={"color": "#2563eb", "width": 1.5},
            customdata=[display_time(stamp) for stamp in bars.index],
            hovertemplate="%{customdata}<br>Close %{y:,.2f}<extra></extra>",
        ))
    else:
        fig = go.Figure(go.Candlestick(
            x=list(range(left, right + 1)), open=visible["open"], high=visible["high"],
            low=visible["low"], close=visible["close"], name="Price", showlegend=False,
            text=[
                f"{display_time(stamp)}<br>O {row.open:,.2f} · H {row.high:,.2f}<br>L {row.low:,.2f} · C {row.close:,.2f}"
                for stamp, row in zip(visible.index, visible.itertuples())
            ],
            hoverinfo="text", whiskerwidth=0,
            increasing_line={"color": "#14532d", "width": 1},
            decreasing_line={"color": "#7f1d1d", "width": 1},
            increasing_fillcolor="#22c55e", decreasing_fillcolor="#ef4444",
        ))
    fig.add_vrect(x0=entry_bar - 0.45, x1=exit_bar + 0.45,
                  fillcolor="#bfdbfe", opacity=0.32, line_width=0, layer="below")

    markers = [
        ("Entry", entry_bar, trade["entry_price"], "#1d4ed8",
         "triangle-down" if trade.get("direction") == "short" else "triangle-up"),
        ("Exit", exit_bar, trade["exit_price"], "#9333ea", "x"),
    ]
    if signal_bar is not None:
        markers.insert(0, ("Signal", signal_bar, bars.at[signal, "close"], "#a45309", "diamond"))
    for label, bar, price, color, symbol in markers:
        if not left <= bar <= right:
            continue
        prices.append(price)
        fig.add_scatter(
            x=[bar], y=[price], customdata=[display_time(bars.index[bar])],
            mode="markers", name=label,
            marker={"size": 13, "symbol": symbol, "color": color,
                    "line": {"width": 1, "color": "#ffffff"}},
            hovertemplate="%{customdata}<br>%{y:,.2f}<extra>%{fullData.name}</extra>",
        )

    for field, label, color in (
        ("initial_stop", "Stop", "#c24156"),
        ("initial_target", "Target", "#0f766e"),
    ):
        price = trade.get(field)
        if not full_run and pd.notna(price) and entry_bar <= right and exit_bar >= left:
            prices.append(price)
            fig.add_scatter(x=[max(entry_bar - 0.45, left - 0.45), min(exit_bar + 0.45, right + 0.45)],
                            y=[price, price], mode="lines", name=label,
                            line={"color": color, "dash": "dash", "width": 1.5},
                            hovertemplate="%{y:,.2f}<extra>%{fullData.name}</extra>")

    low = min(visible["low"].min(), *prices)
    high = max(visible["high"].max(), *prices)
    padding = max((high - low) * 0.12, abs(high) * 0.0001, 0.01)
    ticks = list(range(left, right + 1, max(1, (right - left + 1) // 9)))
    axis_dates = bars.index.tz_convert("Europe/Rome") if bars.index.tz is not None else bars.index
    fig.update_layout(
        height=485, dragmode="pan", hovermode="closest",
        plot_bgcolor="#ffffff", paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#334155"}, margin={"l": 12, "r": 20, "t": 46, "b": 30},
        xaxis={"rangeslider_visible": False, "gridcolor": "#d5deea", "griddash": "dot",
               "range": [left - 0.8, right + 0.8], "tickvals": ticks,
               "ticktext": [axis_dates[i].strftime("%d %b<br>%H:%M") for i in ticks],
               "showspikes": True, "spikemode": "across", "spikesnap": "cursor"},
        yaxis={"side": "right", "gridcolor": "#d5deea", "griddash": "dot", "range": [low - padding, high + padding],
               "tickformat": ",.2f"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02},
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
    view = st.radio("Chart view", ("Trade candles", "Full run overview"), horizontal=True,
                    key=f"{key}_trade_view_{selected}")
    center = "Entry"
    full_run = view == "Full run overview"
    if not full_run:
        entry = pd.Timestamp(trade["entry_time"])
        exit_ = pd.Timestamp(trade["exit_time"])
        if entry in bars.index and exit_ in bars.index and bars.index.get_loc(exit_) - bars.index.get_loc(entry) > 30:
            center = st.radio("Focus on", ("Entry", "Exit"), horizontal=True,
                              key=f"{key}_trade_center_{selected}")
    try:
        figure = build_trade_chart(bars, trade, full_run=full_run, center=center)
    except ValueError as exc:
        st.warning(str(exc))
        return
    st.plotly_chart(figure, use_container_width=True, key=f"{key}_trade_chart_{selected}_{view}_{center}",
                    config={"scrollZoom": True, "displaylogo": False})
    if pd.notna(reason := trade.get("exit_reason")):
        description = {"TP": "Target hit", "SL": "Stop hit", "TIME": "Time exit"}.get(str(reason), str(reason))
        st.caption(f"Exit reason: {description}")
    if full_run:
        st.caption("Closing prices across the full backtest. Switch to Trade candles to inspect individual bars.")
    else:
        st.caption("Hover to see each candle’s time and OHLC. Scroll to zoom within the trade window.")
