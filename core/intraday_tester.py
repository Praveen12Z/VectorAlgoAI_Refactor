"""Market-specific intraday starter tests with a full-session cadence audit."""

from dataclasses import asdict, dataclass
import re

import numpy as np
import pandas as pd

from .backtester_adapter import Position, _resolve_bar_exit
from .mnq_session_data import load_broker_minute_sessions, load_databento_mnq_sessions, load_mnq_sessions


@dataclass(frozen=True)
class Starter:
    id: str
    market: str
    symbol: str
    rule: str
    timeframe: int
    period: int
    hold: int
    cadence: str
    target: tuple[int, int]
    point_value: float | None = None
    tick: float | None = None
    reward_multiple: float = 1.5


STARTERS = (
    Starter("CFD-01", "CFDs", "NAS100 CFD", "EMA reclaim", 15, 12, 60, "week", (5, 7)),
    Starter("CFD-02", "CFDs", "EURUSD CFD", "Channel breakout", 15, 8, 60, "week", (5, 7)),
    Starter("FUT-01", "Index Futures", "MNQ", "EMA reclaim", 15, 5, 25, "day", (3, 4), 2, 0.25),
    Starter("FUT-02", "Index Futures", "MNQ", "Channel breakout", 15, 5, 25, "day", (3, 4), 2, 0.25),
    Starter("CMD-01", "Commodities", "MGC", "Channel breakout", 15, 8, 60, "week", (5, 6), 10, 0.10),
    Starter("CMD-02", "Commodities", "MGC", "EMA reclaim", 5, 12, 35, "day", (2, 3), 10, 0.10),
    Starter("CMD-03", "Commodities", "XAUUSD CFD", "EMA reclaim", 15, 16, 75, "week", (5, 6)),
)
STARTER_MARKETS = ("CFDs", "Index Futures", "Commodities")
EMA_RECLAIM_ID = "FUT-01"
EMA_RECLAIM_DAILY_GOAL = 100


def starter_label(starter):
    floor, ceiling = starter.target
    return f"{starter.symbol} · {starter.rule} · {floor}–{ceiling} trades/{starter.cadence}"


def _signals(bars, starter):
    close = bars.close
    if starter.rule == "EMA reclaim":
        level = close.ewm(span=starter.period, min_periods=starter.period, adjust=False).mean()
        up = close.gt(level) & close.shift().le(level.shift())
        down = close.lt(level) & close.shift().ge(level.shift())
    else:
        high = bars.high.shift().rolling(starter.period).max()
        low = bars.low.shift().rolling(starter.period).min()
        up = close.gt(high)
        down = close.lt(low)
    return up, down


def run_intraday_tester(raw, starter, *, round_turn_cost, cfd_point_value=None, raw_symbol=None):
    """Use one fixed unit, absolute account-currency costs and UTC minute bars."""
    point_value = starter.point_value if starter.point_value is not None else cfd_point_value
    if point_value is None or not np.isfinite(point_value) or point_value <= 0:
        raise ValueError("Enter a positive cash value per price point for one test unit.")
    if not np.isfinite(round_turn_cost) or round_turn_cost <= 0:
        raise ValueError("Enter positive all-in round-trip costs for one test unit.")
    if raw_symbol is not None:
        if starter.point_value is None or not re.fullmatch(starter.symbol + r"[FGHJKMNQUVXZ]\d{1,4}", raw_symbol):
            raise ValueError("Enter the dated futures contract for the selected starter.")
        dataset = load_databento_mnq_sessions(raw, raw_symbol=raw_symbol)
    elif starter.point_value is None:
        dataset = load_broker_minute_sessions(raw)
    else:
        dataset = load_mnq_sessions(raw)
    if not dataset.complete_sessions:
        raise ValueError("The file has no complete 09:30–16:00 New York sessions.")

    ledger = []
    days = []
    for session in dataset.complete_sessions:
        bars = session.candles(starter.timeframe)
        up, down = _signals(bars, starter)
        sides = {stamp: "long" for stamp in up.index[up]}
        sides.update({stamp: "short" for stamp in down.index[down]})
        true_range = pd.concat(
            [bars.high - bars.low, (bars.high - bars.close.shift()).abs(),
             (bars.low - bars.close.shift()).abs()], axis=1
        ).max(axis=1)
        ranges = true_range.rolling(8).mean().dropna().to_dict()
        minutes = session.minutes
        if starter.tick:
            prices_in_ticks = minutes[["open", "high", "low", "close"]].to_numpy() / starter.tick
            if not np.allclose(prices_in_ticks, np.rint(prices_in_ticks), atol=1e-7, rtol=0):
                raise ValueError("Futures prices are off the selected contract's tick grid.")
        position = None
        count = 0
        session_base_net = 0.0
        session_double_cost_net = 0.0
        for offset, (stamp, row) in enumerate(minutes.iterrows()):
            opened_at = stamp - pd.Timedelta(minutes=1)
            side = sides.get(opened_at)
            distance = ranges.get(opened_at, 0)
            if position is None and side and distance > 0 and offset < len(minutes) - 1:
                if starter.tick:
                    distance = int(np.ceil(distance / starter.tick)) * starter.tick
                entry = float(row.open)
                direction = 1 if side == "long" else -1
                target = starter.reward_multiple * distance
                if starter.tick:
                    target = int(np.ceil(target / starter.tick)) * starter.tick
                position = Position(
                    opened_at, side, opened_at, entry, entry - direction * distance,
                    entry + direction * target, distance, distance * point_value + round_turn_cost,
                    1, point_value, round_turn_cost,
                )
                count += 1
            if position is None:
                continue

            expired = opened_at - position.entry_time >= pd.Timedelta(minutes=starter.hold)
            if expired:
                reason, exit_price, exit_time = "Time limit", float(row.open), opened_at
            else:
                reason, exit_price = _resolve_bar_exit(position, row)
                exit_time = stamp
                if reason is None and offset == len(minutes) - 1:
                    reason, exit_price = "Session close", float(row.close)
            if reason is None:
                continue
            sign = 1 if position.direction == "long" else -1
            gross = sign * (exit_price - position.entry_price) * point_value
            base_net = gross - round_turn_cost
            double_cost_net = gross - 2 * round_turn_cost
            ledger.append({
                "session": str(session.date.date()),
                "entry_time": position.entry_time.isoformat(),
                "exit_bar_time": exit_time.isoformat(),
                "side": position.direction, "entry": position.entry_price, "exit": exit_price,
                "reason": reason, "base_net": base_net,
                "double_cost_net": double_cost_net,
            })
            session_base_net += base_net
            session_double_cost_net += double_cost_net
            position = None
        days.append({
            "session": str(session.date.date()), "trades": count,
            "base_net": session_base_net, "double_cost_net": session_double_cost_net,
        })

    dates = pd.DataFrame(days)
    weeks = dates.groupby(pd.to_datetime(dates.session).dt.to_period("W-SUN"))["trades"].agg(["sum", "size"])
    week_rows = [{"week_of": str(period.start_time.date()), "trades": int(row["sum"]),
                  "sessions": int(row["size"]), "included_in_cadence": bool(row["size"] == 5)}
                 for period, row in weeks.iterrows()]
    observed = [day["trades"] for day in days] if starter.cadence == "day" else [
        week["trades"] for week in week_rows if week["included_in_cadence"]
    ]
    low, high = starter.target
    median = float(np.median(observed)) if observed else None
    outcome = "Insufficient sample"
    if len(observed) >= (20 if starter.cadence == "day" else 4):
        outcome = "Below target" if median < low else "Above target band" if median > high else "Within target band"
    base_net = sum(trade["base_net"] for trade in ledger)
    double_cost_net = sum(trade["double_cost_net"] for trade in ledger)
    closed_pnl = np.array([trade["base_net"] for trade in ledger], dtype=float)
    gains = float(closed_pnl[closed_pnl > 0].sum())
    losses = -float(closed_pnl[closed_pnl < 0].sum())
    realized_curve = np.concatenate(([0.0], np.cumsum(closed_pnl)))
    daily_goal = {}
    if starter.id == EMA_RECLAIM_ID:
        daily_goal = {
            "daily_profit_target_usd": EMA_RECLAIM_DAILY_GOAL,
            "average_daily_base_net": base_net / len(days),
            "average_daily_double_cost_net": double_cost_net / len(days),
            "sessions_at_daily_target": sum(day["base_net"] >= EMA_RECLAIM_DAILY_GOAL for day in days),
        }
    return {
        "version": "intraday-starters-v1", "model": starter.id, "rules": asdict(starter),
        "parameter_selection": (
            "Selected on the September 2026 MNQ exploratory replay; fresh validation pending."
            if starter.market == "Index Futures" else "Initial settings; fresh validation pending."
        ),
        "input_sha256": dataset.dataset_sha256, "raw_symbol": raw_symbol,
        "point_value": point_value, "round_turn_cost": round_turn_cost,
        "cadence": starter.cadence, "target": starter.target, "cadence_status": outcome,
        "periods": len(observed), "median_trades": median,
        "at_least_floor_pct": 100 * sum(count >= low for count in observed) / len(observed) if observed else None,
        "in_band_pct": 100 * sum(low <= count <= high for count in observed) / len(observed) if observed else None,
        "base_net": base_net, "double_cost_net": double_cost_net,
        "profit_factor": gains / losses if losses else None,
        "win_rate_pct": float(100 * (closed_pnl > 0).mean()) if ledger else None,
        "max_closed_trade_drawdown_usd": float((np.maximum.accumulate(realized_curve) - realized_curve).max()),
        **daily_goal,
        "days": days, "weeks": week_rows, "trades": ledger,
        "incomplete_sessions": [str(session.date.date()) for session in dataset.sessions if not session.complete],
        "weekdays_without_bars": list(dataset.weekdays_without_session_rows),
    }
