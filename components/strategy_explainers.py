"""Plain-English guides and illustrative setups for the strategy catalog."""

import plotly.graph_objects as go
import streamlit as st


GUIDES = {
    "VA-001": (
        "Look for a market that is already rising. If price dips below its short-term average and then closes back above it, the strategy looks for a buy, provided momentum has recovered too.",
        ("Check the uptrend", "Wait for price to reclaim the average", "Confirm momentum before buying"),
        ([6, 7, 8, 7, 5, 6, 8, 9], 6, {"Short-term average": [5, 5.4, 6, 6.3, 6.2, 6.2, 6.6, 7]}),
    ),
    "VA-002": (
        "Mark the highest price reached in the previous 20 candles. When a candle closes above that ceiling for the first time, the strategy looks to buy at the next open, with a protective stop and a target three times the initial price risk.",
        ("Mark the prior 20-candle high", "Wait for a close above it", "Look for entry at the next open"),
        ([4, 6, 5, 6.5, 5, 6, 8, 9], 6, {"Prior high at signal": [7] * 8}),
    ),
    "VA-003": (
        "Look for a brief sell-off within a longer uptrend. A very low two-day RSI signals a possible buy. The strategy looks to exit when price recovers above its five-day average or the holding limit is reached, with a stop in place.",
        ("Check price is above its 200-day average", "Wait for a sharp dip", "Exit on recovery, timeout, or stop"),
        ([8, 9, 9.5, 9, 8, 6, 7, 9], 5, {"Long-term average": [4, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7]}),
    ),
    "VA-004": (
        "Wait until price is moving in an unusually tight range. If a candle then closes above the upper Bollinger Band, the strategy looks to buy at the next open. It uses a protective stop and a target twice the initial price risk.",
        ("Find unusually narrow bands", "Wait for a close above the upper band", "Look for entry at the next open"),
        ([5, 6, 5.7, 6, 5.9, 6.2, 8, 8.5], 6, {
            "Upper band": [9, 8.2, 7.5, 7, 6.8, 6.7, 7.4, 8.6],
            "Lower band": [2, 3, 4, 4.8, 5.2, 5.4, 5, 4.8],
        }),
    ),
    "VA-005": (
        "Draw a box around the first 15 minutes of the New York session. After the box is set, watch for a five-minute candle to close above the top before 11:00 New York time.",
        ("Mark 09:30–09:45 New York range", "Watch for a close above the high", "Manage one attempt for the day"),
        ([5, 7, 5.5, 6, 5, 6.5, 8, 9], 6, {"Opening range high": [None, None, 7, 7, 7, 7, 7, 7]}),
    ),
    "VA-006": (
        "Start with a confirmed swing high. After price breaks above it, wait for the first qualifying pullback. The buy signal comes when price tests the old ceiling and closes back above it.",
        ("Confirm the old ceiling", "Wait for the break", "Look for the first valid retest"),
        ([4, 5, 7, 5, 6, 9, 8, 7.3, 9], 7, {"Confirmed swing high": [None, None, None, None, 7, 7, 7, 7, 7]}),
    ),
    "VA-007": (
        "Mark yesterday’s session low. Look for a candle that trades below that level but closes back above it during the allowed New York hours. That failed move lower is the buy setup.",
        ("Mark yesterday’s low", "Watch for price to dip below it", "Check the same candle closes back above"),
        ([8, 7, 6, 5.5, 6.2, 7, 7.5], 4, {"Previous-session low": [5] * 7}),
    ),
    "VA-008": (
        "Find a tight three-candle base followed by a strong move up. When price first returns to that base within the allowed window, look for it to close back above the zone before considering a buy.",
        ("Find a tight base", "Confirm a strong move away", "Check the first return to the zone"),
        ([5.2, 5, 5.3, 8.4, 9, 7.5, 6, 8], 6, {
            "Zone high": [None, None, None, 5.7, 5.7, 5.7, 5.7, 5.7],
            "Zone low": [None, None, None, 4.7, 4.7, 4.7, 4.7, 4.7],
        }),
    ),
    "VA-009": (
        "Follow the session’s rising volume-weighted average price, or VWAP. When price dips to that average and closes back above it during the entry window, the strategy looks for the uptrend to continue.",
        ("Check that session VWAP is rising", "Wait for price to touch it", "Look for a close back above VWAP"),
        ([5, 6, 7, 7.8, 7.2, 6.8, 8, 9], 5, {"Session VWAP": [4, 4.3, 4.7, 5.1, 5.5, 6, 6.4, 6.8]}),
    ),
    "VA-010": (
        "When the US jobs report comes in at least 50,000 jobs below expectations, watch gold. The strategy only looks to buy if a five-minute candle closes above the pre-release high during the first eligible window.",
        ("Measure the 30-minute pre-release high", "Check the jobs report against forecasts", "Watch for a gold breakout 15–60 minutes later"),
        None,
    ),
    "PR-001": (
        "Check each market’s own 12-month excess return, meaning its return above the reference cash rate. The research asks whether markets that rose tend to keep rising, and markets that fell tend to keep falling, over the following month.",
        ("Measure each market’s past 12 months", "Use the sign to choose direction", "Evaluate the following month"),
        None,
    ),
    "PR-002": (
        "Look for US stocks trading unusually heavily in the first five minutes. The published research uses the opening candle’s direction and range to plan a breakout trade. VectorAlgoAI currently screens candidates.",
        ("Filter for eligible stocks", "Rank by relative opening volume", "Study breakouts in the opening candle’s direction"),
        None,
    ),
}


def render_strategy_example(strategy_id, example, steps):
    if example is None:
        st.markdown("**How the setup unfolds**")
        for index, (column, step) in enumerate(zip(st.columns(len(steps)), steps), start=1):
            with column:
                with st.container(border=True):
                    st.write(f"**{index}.** {step}")
        return

    closes, signal, guides = example
    bars = list(range(1, len(closes) + 1))
    fig = go.Figure()
    for name, values in guides.items():
        fig.add_scatter(x=bars, y=values, mode="lines", name=name,
                        line={"width": 2, "dash": "dash"})
    if strategy_id in {"VA-006", "VA-007", "VA-008", "VA-009"}:
        low = {"VA-006": 7, "VA-007": 4.4, "VA-008": 5.3, "VA-009": 6}[strategy_id]
        fig.add_scatter(x=[bars[signal]] * 2, y=[low, closes[signal]], mode="lines",
                        name="Signal bar low to close", line={"color": "#64748b", "width": 4})
    fig.add_scatter(x=bars, y=closes, mode="lines+markers", name="Example close",
                    line={"color": "#2563eb", "width": 3})
    fig.add_scatter(x=[bars[signal]], y=[closes[signal]], mode="markers",
                    name="Setup signal", marker={"size": 12, "color": "#0f766e", "symbol": "diamond"})
    fig.update_layout(height=255, margin={"l": 18, "r": 18, "t": 8, "b": 12},
                      legend={"orientation": "h", "y": -0.25},
                      xaxis={"title": "Example bars", "dtick": 1, "fixedrange": True},
                      yaxis={"showticklabels": False, "fixedrange": True})
    st.caption("Illustrative setup · synthetic prices · setup marker shows the signal")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False},
                    key=f"strategy_example_{strategy_id}")
    st.caption(" → ".join(steps))
