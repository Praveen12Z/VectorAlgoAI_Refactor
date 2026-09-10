# core/backtester_adapter.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .strategy_config import StrategyConfig


@dataclass
class Position:
    direction: str          # "long" or "short"
    entry_time: pd.Timestamp
    entry_price: float
    sl: float | None
    tp: float | None
    risk_per_unit: float | None  # distance to stop (for RR)
    size: float
    risk_amount: float
    point_value: float
    

def _get_val(row: pd.Series, token):
    if isinstance(token, (int, float)):
        return float(token)
    if isinstance(token, str):
        try:
            return float(token)
        except ValueError:
            return float(row[token])
    return float(token)


def _check_conditions(row: pd.Series, conds: List[Dict]) -> bool:
    if not conds:
        return False
    for c in conds:
        left = _get_val(row, c.get("left"))
        right = _get_val(row, c.get("right"))
        op = c.get("op", "==")
        if op == ">":
            ok = left > right
        elif op == "<":
            ok = left < right
        elif op == ">=":
            ok = left >= right
        elif op == "<=":
            ok = left <= right
        elif op == "==":
            ok = left == right
        else:
            ok = False
        if not ok:
            return False
    return True


def _build_exits(row: pd.Series, cfg: StrategyConfig, side: str) -> Tuple[float | None, float | None, float | None]:
    """
    Return (sl, tp, risk_per_unit) for the given side based on ATR rules.
    """
    exit_rules = (cfg.raw.get("exit", {}) or {}).get(side, []) or []
    atr_val = None
    entry_price = row["close"]
    sl = tp = None

    for rule in exit_rules:
        if rule.get("type") in ("atr_sl", "atr_tp"):
            atr_col = rule.get("atr_col")
            mult = float(rule.get("multiple", 2.0))
            if atr_col in row.index:
                atr_val = float(row[atr_col])
            else:
                continue

            if rule["type"] == "atr_sl":
                if side == "long":
                    sl = entry_price - mult * atr_val
                else:
                    sl = entry_price + mult * atr_val
            elif rule["type"] == "atr_tp":
                if side == "long":
                    tp = entry_price + mult * atr_val
                else:
                    tp = entry_price - mult * atr_val

    risk_per_unit = None
    if sl is not None:
        if side == "long":
            risk_per_unit = entry_price - sl
        else:
            risk_per_unit = sl - entry_price

    return sl, tp, risk_per_unit


def _resolve_bar_exit(position: Position, row: pd.Series) -> Tuple[str | None, float | None]:
    """Resolve protective exits from OHLC data using a conservative policy.

    Candle data does not reveal whether the high or low occurred first. When a
    stop and target are both touched inside the same candle, the stop is assumed
    to have occurred first. This avoids manufacturing optimistic backtests.
    """
    high = float(row["high"])
    low = float(row["low"])
    open_price = float(row["open"])

    if position.direction == "long":
        stop_hit = position.sl is not None and low <= position.sl
        target_hit = position.tp is not None and high >= position.tp
        if stop_hit:
            return "SL", min(open_price, float(position.sl))
        if target_hit:
            return "TP", float(position.tp)
    else:
        stop_hit = position.sl is not None and high >= position.sl
        target_hit = position.tp is not None and low <= position.tp
        if stop_hit:
            return "SL", max(open_price, float(position.sl))
        if target_hit:
            return "TP", float(position.tp)

    return None, None


def _open_position(
    row: pd.Series,
    cfg: StrategyConfig,
    side: str,
    ts: pd.Timestamp,
    equity: float,
) -> Position:
    sl, tp, risk_per_unit = _build_exits(row, cfg, side)
    if risk_per_unit is None or not np.isfinite(risk_per_unit) or risk_per_unit <= 0:
        raise ValueError(
            "The strategy has no executable protective stop, so risk-based position "
            "sizing cannot be calculated. Add a valid stop-loss before backtesting."
        )

    risk_cfg = cfg.raw.get("risk", {}) or {}
    risk_pct = float(risk_cfg.get("risk_per_trade_pct", 0.0))
    point_value = float(risk_cfg.get("point_value", 1.0))
    if not 0 < risk_pct <= 100:
        raise ValueError("risk_per_trade_pct must be greater than 0 and no more than 100.")
    if not np.isfinite(point_value) or point_value <= 0:
        raise ValueError("risk.point_value must be a positive number.")

    risk_amount = equity * risk_pct / 100.0
    size = risk_amount / (risk_per_unit * point_value)
    return Position(
        direction=side,
        entry_time=ts,
        entry_price=float(row["close"]),
        sl=sl,
        tp=tp,
        risk_per_unit=risk_per_unit,
        size=size,
        risk_amount=risk_amount,
        point_value=point_value,
    )


def _grade_strategy(total_ret: float, pf: float, win_rate: float, num_trades: int) -> str:
    if num_trades < 10:
        return "D"
    if pf > 1.6 and total_ret > 15 and win_rate > 50:
        return "A"
    if pf > 1.3 and total_ret > 5:
        return "B"
    if pf > 1.05:
        return "C"
    return "D"


def run_backtest_v2(df: pd.DataFrame, cfg: StrategyConfig):
    """
    Very simple bar-by-bar backtester using YAML conditions.
    - Only supports one open position at a time.
    - Evaluates entries at close.
    - Resolves protective exits from the following candles' OHLC range.
    - Assumes the stop was hit first when stop and target occur in one candle.
    """
    raw = cfg.raw or {}
    entry_block = raw.get("entry", {}) or {}

    long_conds = entry_block.get("long", []) or []
    short_conds = entry_block.get("short", []) or []

    risk_cfg = raw.get("risk", {}) or {}
    capital = float(risk_cfg.get("capital", 10000.0))
    if not np.isfinite(capital) or capital <= 0:
        raise ValueError("risk.capital must be a positive number.")

    position: Position | None = None
    trades: List[Dict] = []
    current_equity = capital

    for ts, row in df.iterrows():
        # close existing position?
        if position is not None:
            exit_reason, exit_price = _resolve_bar_exit(position, row)

            # simple time-based fail-safe: close at last bar
            is_last_bar = ts == df.index[-1]

            if exit_reason is not None or is_last_bar:
                if exit_price is None:
                    exit_price = float(row["close"])
                if position.direction == "long":
                    pnl_per_unit = exit_price - position.entry_price
                else:
                    pnl_per_unit = position.entry_price - exit_price

                pnl = pnl_per_unit * position.size * position.point_value
                rr = pnl / position.risk_amount
                current_equity += pnl

                trades.append(
                    {
                        "entry_time": position.entry_time,
                        "exit_time": ts,
                        "direction": position.direction,
                        "entry_price": position.entry_price,
                        "exit_price": exit_price,
                        "size": position.size,
                        "risk_amount": position.risk_amount,
                        "point_value": position.point_value,
                        "pnl": pnl,
                        "rr": rr,
                        "exit_reason": exit_reason or "time_exit",
                    }
                )
                position = None

                # after closing, continue to next loop iteration to allow re-entry
                continue

        # if flat, check for entries
        if position is None:
            if _check_conditions(row, long_conds):
                position = _open_position(row, cfg, "long", ts, current_equity)
            elif _check_conditions(row, short_conds):
                position = _open_position(row, cfg, "short", ts, current_equity)

    trades_df = pd.DataFrame(trades)
    if trades_df.empty:
        metrics = {
            "total_return_pct": 0.0,
            "profit_factor": 0.0,
            "win_rate_pct": 0.0,
            "max_drawdown_pct": 0.0,
            "num_trades": 0,
            "grade": "D",
            "execution_model": "ohlc_stop_first",
            "risk_sizing_applied": False,
            "costs_included": False,
            "oos_passed": False,
        }
        weaknesses = ["Too few trades to evaluate.", "Strategy might be over-filtered."]
        suggestions = ["Relax entry conditions or test on more data."]
        return metrics, weaknesses, suggestions, trades_df

    # equity & metrics
    pnl = trades_df["pnl"].values
    equity = capital + np.cumsum(pnl)
    peak = np.maximum.accumulate(equity)
    dd = (equity - peak) / peak
    max_dd_pct = float(dd.min() * 100.0)

    gross_profit = trades_df.loc[trades_df["pnl"] > 0, "pnl"].sum()
    gross_loss = -trades_df.loc[trades_df["pnl"] < 0, "pnl"].sum()
    if gross_loss <= 0:
        pf = float("inf") if gross_profit > 0 else 0.0
    else:
        pf = float(gross_profit / gross_loss)

    total_return_pct = float((equity[-1] - capital) / capital * 100.0)
    num_trades = len(trades_df)
    win_rate_pct = float((trades_df["pnl"] > 0).mean() * 100.0)

    grade = _grade_strategy(total_return_pct, pf, win_rate_pct, num_trades)

    metrics = {
        "total_return_pct": total_return_pct,
        "profit_factor": pf,
        "win_rate_pct": win_rate_pct,
        "max_drawdown_pct": max_dd_pct,
        "num_trades": num_trades,
        "grade": grade,
        "execution_model": "ohlc_stop_first",
        "risk_sizing_applied": True,
        "costs_included": False,
        "oos_passed": False,
    }

    weaknesses: List[str] = []
    suggestions: List[str] = []

    if num_trades < 20:
        weaknesses.append("Too few trades to determine stability (sample < 20).")
        suggestions.append("Test on more history or trade more frequently.")
    if pf < 1.10:
        weaknesses.append("No demonstrated baseline edge (profit factor < 1.10 before costs).")
        suggestions.append("Test one entry or exit change at a time, then add realistic costs.")
    if win_rate_pct < 45 and pf < 1.10:
        weaknesses.append("Low win rate is not being offset by sufficient winner size.")
        suggestions.append("Test entry selectivity separately from stop and target changes.")
    if max_dd_pct < -20:
        weaknesses.append("Max drawdown deeper than -20%.")
        suggestions.append("Reduce risk per trade or add volatility filters.")

    return metrics, weaknesses, suggestions, trades_df
