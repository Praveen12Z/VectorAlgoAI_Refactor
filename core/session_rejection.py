"""Prior-session high rejection using completed bars and New York session times."""

import re
from datetime import time
from math import isfinite

import pandas as pd


# Match the supported rule form as a whole. An added constraint must be reviewed,
# never dropped from an executable draft.
BRIEF = re.compile(
    r"I want to backtest a failed breakout on (?P<market>XAUUSD|NAS100|US30) using 15-minute candles\. "
    r"Mark the high of the previous completed New York trading day\. "
    r"Between 09:30 and 12:00 New York time, if a candle trades above that high and closes back below it, "
    r"enter short at the next candle's open, only if that open is before 12:00\. "
    r"Put the stop loss (?:(?:one minimum price increment)|(?P<buffer>\d+(?:\.\d+)?) price points?) "
    r"above the signal candle's high and target (?P<target>\d+(?:\.\d+)?)R\. "
    r"Allow one trade per day\. Close any remaining position at 16:00 New York time\. "
    r"Use a simulated account of \$?(?P<capital>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?) and risk "
    r"(?P<risk>\d+(?:\.\d+)?)% per trade\.?",
    re.IGNORECASE,
)
MORNING_START = time(9, 30)
ENTRY_CUTOFF = time(12)
SESSION_END = time(16)
BAR = pd.Timedelta(minutes=15)


def build_rejection_schema(text):
    match = BRIEF.fullmatch(" ".join(text.strip().replace("’", "'").split()))
    if not match:
        return None
    market = match["market"].upper()
    buffer = float(match["buffer"]) if match["buffer"] else (0.10 if market == "XAUUSD" else None)
    if buffer is not None and (not isfinite(buffer) or buffer <= 0):
        buffer = None
    target = float(match["target"])
    if not isfinite(target) or target <= 0:
        return None
    assumptions = [{
        "field": "Previous trading day",
        "value": "Immediately preceding observed 09:30–16:00 New York session. Both sessions must be complete.",
        "reason": "The brief does not specify whether the prior high includes overnight trading.",
    }]
    if match["buffer"] is None and buffer is not None:
        assumptions.append({
            "field": "Research stop buffer",
            "value": buffer,
            "reason": "Use 0.10 price points as a modeling assumption for the XAUUSD gold futures proxy. Confirm it or state an explicit buffer.",
        })
    return {
        "source_text": text.strip(), "market": market, "timeframe": "15m", "direction": "short",
        "risk": {
            "capital": float(match["capital"].replace(",", "")),
            "risk_per_trade_pct": float(match["risk"]),
        },
        "assumptions": assumptions,
        "components": [
            {"category": "entry", "component": "prior_session_high_rejection", "params": {
                "direction": "short", "timezone": "America/New_York", "session": "09:30–16:00",
                "next_open_before": "12:00", "maximum_entries_per_day": 1,
            }},
            {"category": "risk", "component": "signal_high_stop", "params": {"buffer_points": buffer}},
            {"category": "risk", "component": "rr_target", "params": {"rr": target}},
            {"category": "exit", "component": "session_close_exit", "params": {"close": "16:00 New York"}},
        ],
    }


def session_index(index):
    if not isinstance(index, pd.DatetimeIndex) or index.tz is None:
        raise ValueError("This setup requires timezone-aware, bar-open timestamps from a 15-minute feed.")
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError("This setup requires unique chronological 15-minute bars.")
    return index.tz_convert("America/New_York")


def rejection_features(df, buffer_points):
    local = session_index(df.index)
    local_time = local.time
    regular = (local_time >= MORNING_START) & (local_time < SESSION_END)
    bars = df.loc[regular, ["high", "close"]]
    dates = local[regular].normalize()
    complete = pd.Series(False, index=dates.unique(), dtype=bool)
    for date, times in pd.Series(local[regular], index=dates).groupby(level=0):
        start = pd.Timestamp.combine(date.date(), MORNING_START).tz_localize(local.tz)
        expected = pd.date_range(start, periods=26, freq=BAR)
        complete.loc[date] = pd.DatetimeIndex(times).equals(expected)

    high = bars["high"].groupby(dates).max().where(complete).shift()
    level = pd.Series(high.reindex(local.normalize()).to_numpy(), index=df.index)
    eligible = pd.Series(complete.reindex(local.normalize(), fill_value=False).to_numpy(), index=df.index)
    next_open = local + BAR
    signal = regular & eligible & (next_open.time < ENTRY_CUTOFF) & df["high"].gt(level) & df["close"].lt(level)
    return df.assign(
        prior_session_rejection=signal.astype(int),
        setup_level=level,
        rejection_stop=df["high"] + buffer_points,
        session_close=regular & eligible & (next_open.time == SESSION_END),
    )
