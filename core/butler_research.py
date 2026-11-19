"""Exploratory translation of Butler's 5-minute Nasdaq reversal setup."""
from collections import Counter
from hashlib import sha256
from io import BytesIO
import json

import numpy as np
import pandas as pd

from .backtester_adapter import ExecutionCostModel

VERSION = "butler-mnq-1"
POINT_VALUE = 2.0
START_EQUITY = 100_000
COSTS = ExecutionCostModel(0.25, 0.25, 1.50)
RULES = {
    "Session": "09:30–16:00 America/New_York. Require all 390 minute bars; flatten at 16:00.",
    "Zone": "Latest confirmed 15-minute two-left/two-right pivot low/high, with a 10-point band on each side. Fresh test requires the preceding 5-minute bar to be outside the band.",
    "Momentum": "At the test, the prior two 5-minute closes moved toward the zone and the mean candle body of the latest two bars is smaller than that of the preceding two.",
    "Confirmation": "Within six more bars, close across the most recent confirmed two-left/two-right 5-minute pivot known at the test. Crossing candle must close in the trade direction.",
    "Base and entry": "The next two bars must stay inside the confirmation candle's range and have smaller bodies. The following bar must close beyond the base in the trade direction. Fill at the next minute open.",
    "Management": "One position at a time. 0.5% of current equity, rounded down to an even contract count with base costs included in planned risk. From the fill: 50-point stop, half off at +50 points, remaining half at +100 points with stop moved to entry.",
    "Daily limit": "At most three entries and stop after two wins or two losses. Classify closed positions by net P&L. A zero-dollar trade still counts toward the three-entry limit.",
    "Fill policy": "Minute OHLC; adverse stop wins an ambiguous minute and may gap through its level. If TP1 and the new breakeven stop are both in the same minute, assume the runner reaches breakeven first. Targets get their stated price. Deduct costs in cash.",
}


PAUSE_RULES = {
    "two_candle": RULES["Base and entry"],
    "one_candle": (
        "The next bar must close against the trade direction. The immediately following bar "
        "must close in the trade direction beyond both the pullback close and the broken swing. "
        "Fill at the next minute open."
    ),
}


def _load_minutes(raw):
    bars = pd.read_csv(BytesIO(raw), sep=";", header=None,
                       names=["stamp", "open", "high", "low", "close", "volume"], index_col=False,
                       on_bad_lines="error")
    if bars.empty:
        raise ValueError("No minute candles found.")
    stamps = pd.to_datetime(bars.pop("stamp"), format="%Y%m%d %H%M%S", utc=True)
    bars = bars.apply(pd.to_numeric, errors="raise")
    if (stamps.duplicated().any() or not stamps.eq(stamps.dt.floor("min")).all()
            or not np.isfinite(bars.to_numpy()).all()
            or (bars.high < bars[["open", "low", "close"]].max(axis=1)).any()
            or (bars.low > bars[["open", "close"]].min(axis=1)).any()
            or (bars.low <= 0).any() or (bars.volume < 0).any()):
        raise ValueError("Use unique minute-end stamps and valid OHLCV prices/volume.")
    bars.index = stamps.dt.tz_convert("America/New_York")
    return bars.sort_index()


def _aggregate(bars, interval):
    return bars.resample(interval, closed="right", label="right").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"}
    )


def _pivots(bars):
    # A pivot only becomes visible at the close of its second right-hand bar.
    levels = {}
    for field, sign in (("low", -1), ("high", 1)):
        values = sign * bars[field]
        candidate = values.shift(2)
        confirmed = (candidate > values) & (candidate > values.shift(1))
        confirmed &= (candidate > values.shift(3)) & (candidate > values.shift(4))
        levels[field] = (sign * candidate).where(confirmed)
    return pd.DataFrame(levels, index=bars.index)


def _signals(five, zones, funnel, swing_audit, pause_model):
    swings = _pivots(five).ffill().shift(1)
    zones = zones.reindex(five.index, method="ffill").shift(1)
    rows = list(five.itertuples())
    bodies = (five.close - five.open).abs().to_numpy()
    scheduled = {}
    for side, field, swing_field in ((1, "low", "high"), (-1, "high", "low")):
        eligible_from = 3
        for i in range(3, len(rows)):
            if i < eligible_from:
                continue
            zone = zones[field].iloc[i]
            previous, current = rows[i-1:i+1]
            if pd.isna(zone) or not (current.low <= zone + 10 and current.high >= zone - 10):
                continue
            if previous.low <= zone + 10 and previous.high >= zone - 10:
                continue
            funnel["fresh zone tests"] += 1
            if (side * (previous.close - rows[i-3].close) >= 0
                    or bodies[i-1:i+1].mean() >= bodies[i-3:i-1].mean()):
                continue
            funnel["momentum slowdowns"] += 1
            level = swings[swing_field].iloc[i]
            for j in range(i+1, min(i+7, len(rows))):
                leg = rows[j]
                if not (side * (rows[j-1].close - level) <= 0 < side * (leg.close - level)
                        and side * (leg.close - leg.open) > 0):
                    continue
                funnel["swing breaks"] += 1
                audit = {"zone_test": current.Index.isoformat(), "zone": float(zone),
                         "swing_break": leg.Index.isoformat(), "swing_level": float(level),
                         "side": "long" if side == 1 else "short", "base": "session ended"}
                swing_audit.append(audit)
                base_length = 2 if pause_model == "two_candle" else 1
                base_end = j + 1 + base_length
                if base_end > len(rows):
                    break
                base = rows[j+1:base_end]
                eligible_from = base_end + 1
                if pause_model == "two_candle":
                    high, low = max(x.high for x in base), min(x.low for x in base)
                    outside_leg = high > leg.high or low < leg.low
                    larger_body = max(bodies[j+1:base_end]) >= bodies[j]
                    audit.update(base_outside_leg=bool(outside_leg), base_body_too_large=bool(larger_body))
                    base_passed = not (outside_leg or larger_body)
                    edge = high if side == 1 else low
                else:
                    pause = base[0]
                    base_passed = side * (pause.close - pause.open) < 0
                    edge = max(pause.close, level) if side == 1 else min(pause.close, level)
                    audit.update(pullback_close=float(pause.close), continuation_level=float(edge))
                audit["base"] = "passed" if base_passed else "failed"
                if not base_passed:
                    break
                funnel["bases confirmed"] += 1
                if base_end < len(rows):
                    signal = rows[base_end]
                    if pause_model == "one_candle":
                        audit.update(continuation_time=signal.Index.isoformat(),
                                     continuation_close=float(signal.close))
                    if side * (signal.close - edge) > 0 and side * (signal.close - signal.open) > 0:
                        funnel["entry signals"] += 1
                        scheduled.setdefault(signal.Index, []).append(side)
                break
    return scheduled


def _trade(session, start, signal, side, size, costs):
    fill = float(session.iloc[start].open)
    initial_stop, tp1, tp2 = (fill + side * offset for offset in (-50, 50, 100))
    stop = initial_stop
    exits = []
    for bar in session.iloc[start:].itertuples():
        best, worst = (bar.high, bar.low) if side == 1 else (bar.low, bar.high)
        if exits and side * (bar.open - tp2) >= 0:
            exits.append((bar.Index, tp2, size // 2, "TP2"))
            break
        if not exits and side * (bar.open - tp1) >= 0:
            exits.append((bar.Index, tp1, size // 2, "TP1"))
            stop = fill
            if side * (bar.open - tp2) >= 0:
                exits.append((bar.Index, tp2, size // 2, "TP2"))
                break
        if side * (worst - stop) <= 0:
            reason = "Stop" if not exits else "Breakeven stop"
            price = bar.open if side * (bar.open - stop) < 0 else stop
            exits.append((bar.Index, price, size if not exits else size // 2, reason))
            break
        if not exits and side * (best - tp1) >= 0:
            exits.append((bar.Index, tp1, size // 2, "TP1"))
            stop = fill
            if side * (worst - stop) <= 0:
                exits.append((bar.Index, stop, size // 2, "Breakeven stop"))
                break
        if exits and side * (best - tp2) >= 0:
            exits.append((bar.Index, tp2, size // 2, "TP2"))
            break
    remaining = size - sum(x[2] for x in exits)
    if remaining:
        exits.append((session.index[-1], float(session.iloc[-1].close), remaining, "Session close"))
    gross = sum(side * (price - fill) * quantity * POINT_VALUE for _, price, quantity, _ in exits)
    return {
        "signal_time": signal.isoformat(),
        "entry_time": (session.index[start] - pd.Timedelta(minutes=1)).isoformat(),
        "exit_bar_end": exits[-1][0].isoformat(), "side": "long" if side == 1 else "short",
        "contracts": size, "entry": fill, "initial_stop": initial_stop,
        "cost_usd": round(costs * size, 2), "net_usd": round(gross - costs * size, 2),
        "exits": [{"bar_end": stamp.isoformat(), "price": price, "contracts": quantity, "reason": reason}
                  for stamp, price, quantity, reason in exits],
    }, exits[-1][0]


def _execute(days, costs):
    equity, ledger = START_EQUITY, []
    counts = Counter({key: 0 for key in ("no next session minute", "conflicting signals",
                                        "daily limit", "open position", "size below two", "fills")})
    for day, signals in days:
        entries = wins = losses = 0
        occupied_through = day.index[0] - pd.Timedelta(minutes=1)
        for signal, sides in sorted(signals.items()):
            start = day.index.searchsorted(signal, side="right")
            if start == len(day):
                counts["no next session minute"] += len(sides)
            elif len(sides) > 1:
                counts["conflicting signals"] += len(sides)
            elif entries >= 3 or max(wins, losses) >= 2:
                counts["daily limit"] += 1
            elif day.index[start] <= occupied_through:
                counts["open position"] += 1
            else:
                size = 2 * int(equity * 0.005 // (2 * (50 * POINT_VALUE + costs)))
                if size < 2:
                    counts["size below two"] += 1
                    continue
                trade, occupied_through = _trade(day, start, signal, sides[0], size, costs)
                ledger.append(trade)
                counts["fills"] += 1
                entries += 1
                equity += trade["net_usd"]
                wins += trade["net_usd"] > 0
                losses += trade["net_usd"] < 0
    profits = [t["net_usd"] for t in ledger]
    path = pd.Series([START_EQUITY, *np.asarray(profits).cumsum() + START_EQUITY])
    negative = -sum(p for p in profits if p < 0)
    month_counts = dict.fromkeys((day.index[0].strftime("%Y-%m") for day, _ in days), 0)
    for trade in ledger:
        month_counts[trade["entry_time"][:7]] += 1
    return {"execution": dict(counts), "monthly_trades": month_counts, "trades": ledger,
            "net_usd": round(sum(profits), 2), "cost_usd": round(sum(t["cost_usd"] for t in ledger), 2),
            "profit_factor": round(sum(p for p in profits if p > 0) / negative, 4) if negative else None,
            "closed_trade_drawdown_usd": round(float((path.cummax() - path).max()), 2)}


def run_butler_research(raw, *, pause_model="two_candle"):
    if pause_model not in PAUSE_RULES:
        raise ValueError("Unknown MNQ reversal base rule.")
    bars = _load_minutes(raw)
    rth = bars.between_time("09:30", "16:00", inclusive="right")
    dates = [day for date, day in rth.groupby(rth.index.normalize()) if date.weekday() < 5]
    full_days = [day for day in dates if len(day) == 390]
    if not full_days:
        raise ValueError("No complete Monday–Friday 09:30–16:00 New York sessions.")
    funnel = Counter({key: 0 for key in ("fresh zone tests", "momentum slowdowns",
                                       "swing breaks", "bases confirmed", "entry signals")})
    history = []
    days = []
    swing_audit = []
    for day in full_days:
        history.append(_pivots(_aggregate(day, "15min")))
        zones = pd.concat(history).ffill()
        # Make the previous session's level available from the opening bell.
        five = _aggregate(day, "5min")
        days.append((day, _signals(five, zones, funnel, swing_audit, pause_model)))
    result = {
        "model": VERSION if pause_model == "two_candle" else "butler-mnq-2", "source": "Richard Butler, Market Masters presentation",
        "status": "Exploratory, one contract month; no untouched validation",
        "dataset_sha256": sha256(raw).hexdigest(), "coverage_start": bars.index[0].isoformat(),
        "coverage_end": bars.index[-1].isoformat(), "minute_rows": len(bars),
        "complete_sessions": len(full_days), "complete_session_dates": [str(d.index[0].date()) for d in full_days],
        "excluded_incomplete_sessions": [str(d.index[0].date()) for d in dates if len(d) != 390],
        "session_calendar": "Weekdays with observed rows; absent weekdays in supplied date span listed separately.",
        "weekdays_without_rth_rows": sorted(str(d.date()) for d in
            pd.bdate_range(bars.index[0].normalize(), bars.index[-1].normalize())
            if d not in {day.index[0].normalize() for day in dates}),
        "five_minute_bars": 78 * len(full_days),
        "rules": {**RULES, "Base and entry": PAUSE_RULES[pause_model]}, "signal_counts": dict(funnel),
        "swing_break_audit": swing_audit,
        "base_cost_model": COSTS.as_dict(), "starting_equity_usd": START_EQUITY,
        "base": _execute(days, COSTS.cash_per_unit(POINT_VALUE)),
        "double_cost": _execute(days, 2 * COSTS.cash_per_unit(POINT_VALUE)),
    }
    if pause_model == "one_candle":
        result["pause_model"] = pause_model
        result["status"] = "In-sample comparison designed after reviewing v1 rejections; no untouched validation"
    result["record_sha256"] = sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return result
