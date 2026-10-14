"""Conservative bar-based backtester: close signals, next-open entries.

Intrabar ambiguity resolves against the trader (stop before target).
This is not tick-level simulation; explicitly configure contract multiplier and costs.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .strategy_config import StrategyConfig


def _value(row, token):
    try:
        return float(token)
    except (ValueError, TypeError):
        return float(row[token])


def _matches(row, rules):
    if not rules:
        return False
    ops = {">": lambda a,b: a>b, "<": lambda a,b: a<b,
           ">=": lambda a,b: a>=b, "<=": lambda a,b: a<=b,
           "==": lambda a,b: a==b}
    for rule in rules:
        op = rule.get("op")
        if op not in ops:
            raise ValueError(f"Unsupported operator: {op}")
        a, b = _value(row, rule["left"]), _value(row, rule["right"])
        if not (math.isfinite(a) and math.isfinite(b) and ops[op](a,b)):
            return False
    return True


def _levels(signal, entry, cfg, side):
    stop = target = None
    direction = 1 if side == "long" else -1
    for rule in (cfg.raw.get("exit", {}) or {}).get(side, []):
        kind = rule.get("type")
        if kind not in ("atr_sl", "atr_tp"):
            raise ValueError(f"Unsupported exit rule: {kind}")
        atr = float(signal[rule["atr_col"]])
        mult = float(rule["multiple"])
        if not math.isfinite(atr) or atr <= 0 or not math.isfinite(mult) or mult <= 0:
            raise ValueError("ATR and exit multiple must be positive finite numbers")
        if kind == "atr_sl":
            stop = entry - direction * atr * mult
        else:
            target = entry + direction * atr * mult
    if stop is None:
        raise ValueError("ATR stop required for risk sizing")
    return stop, target


def run_backtest_v2(df: pd.DataFrame, cfg: StrategyConfig):
    if df.empty or not {"open","high","low","close"}.issubset(df):
        raise ValueError("Nonempty OHLC data required")
    if not df.index.is_monotonic_increasing or df.index.has_duplicates:
        raise ValueError("OHLC timestamps must be unique and sorted")
    raw = cfg.raw or {}
    risk = raw.get("risk", {}) or {}
    capital = float(risk.get("capital", 10000))
    risk_pct = float(risk.get("risk_per_trade_pct", 1))
    multiplier = float(risk.get("contract_multiplier", 1))
    commission = float(risk.get("commission_per_unit_per_side", 0))
    slippage = float(risk.get("slippage_points_per_side", 0))
    integer_units = bool(risk.get("integer_units", False))
    if not all(map(math.isfinite, (capital,risk_pct,multiplier,commission,slippage))):
        raise ValueError("Nonfinite risk parameters")
    if capital <= 0 or not 0 < risk_pct <= 100 or multiplier <= 0 or commission < 0 or slippage < 0:
        raise ValueError("Invalid risk parameters")

    cash = capital
    pending = None
    position = None
    trades = []
    entries = raw.get("entry", {}) or {}
    for i, (ts, row) in enumerate(df.iterrows()):
        o, h, l, c = (float(row[k]) for k in ("open","high","low","close"))
        if not all(map(math.isfinite, (o,h,l,c))) or l > min(o,c) or h < max(o,c) or h < l:
            raise ValueError("Invalid OHLC bar")

        if position is None and pending is not None:
            side, signal = pending
            pending = None
            direction = 1 if side == "long" else -1
            entry = o + direction * slippage
            stop, target = _levels(signal, entry, cfg, side)
            risk_per_unit = abs(entry-stop)*multiplier + 2*commission + 2*slippage*multiplier
            if risk_per_unit > 0 and cash > 0:
                quantity = cash*risk_pct/100/risk_per_unit
                if integer_units:
                    quantity = math.floor(quantity)
                if quantity > 0:
                    position = dict(side=side, direction=direction, entry=entry,
                                    stop=stop, target=target, quantity=quantity,
                                    entry_time=ts, risk=quantity*risk_per_unit)

        if position is not None:
            p = position
            direction = p["direction"]
            if direction == 1:
                stop_hit = l <= p["stop"]
                target_hit = p["target"] is not None and h >= p["target"]
                stop_fill = min(o, p["stop"])
                target_fill = max(o, p["target"]) if p["target"] is not None else None
            else:
                stop_hit = h >= p["stop"]
                target_hit = p["target"] is not None and l <= p["target"]
                stop_fill = max(o, p["stop"])
                target_fill = min(o, p["target"]) if p["target"] is not None else None
            reason = "SL" if stop_hit else ("TP" if target_hit else None)
            if i == len(df)-1 and reason is None:
                reason = "time_exit"
            if reason:
                raw_exit = stop_fill if reason == "SL" else (target_fill if reason == "TP" else c)
                exit_price = raw_exit - direction*slippage
                gross = direction*(exit_price-p["entry"])*p["quantity"]*multiplier
                fees = 2*commission*p["quantity"]
                pnl = gross-fees
                cash += pnl
                trades.append(dict(entry_time=p["entry_time"], exit_time=ts,
                    direction=p["side"], entry_price=p["entry"], exit_price=exit_price,
                    quantity=p["quantity"], gross_pnl=gross, fees=fees,
                    pnl=pnl, rr=pnl/p["risk"], exit_reason=reason))
                position = None
                continue

        if position is None and i < len(df)-1:
            if _matches(row, entries.get("long", [])):
                pending = ("long", row.copy())
            elif _matches(row, entries.get("short", [])):
                pending = ("short", row.copy())

    trades_df = pd.DataFrame(trades, columns=["entry_time","exit_time","direction",
        "entry_price","exit_price","quantity","gross_pnl","fees","pnl","rr","exit_reason"])
    if trades_df.empty:
        return dict(total_return_pct=0.,profit_factor=0.,win_rate_pct=0.,
                    max_drawdown_pct=0.,num_trades=0,grade="D"), [
                    "Too few trades to evaluate."], ["Check signal rules and history."], trades_df
    pnl = trades_df["pnl"].to_numpy()
    equity = np.r_[capital, capital+np.cumsum(pnl)]
    peaks = np.maximum.accumulate(equity)
    dd = np.divide(equity-peaks, peaks, out=np.zeros_like(equity), where=peaks>0)
    gains = float(pnl[pnl>0].sum())
    losses = float(-pnl[pnl<0].sum())
    pf = gains/losses if losses else (float("inf") if gains else 0.)
    ret = float((equity[-1]/capital-1)*100)
    wr = float(np.mean(pnl>0)*100)
    n = len(pnl)
    grade = ("A" if n>=30 and pf>1.6 and ret>15 and wr>50 else
             "B" if n>=20 and pf>1.3 and ret>5 else
             "C" if n>=10 and pf>1.05 else "D")
    metrics = dict(total_return_pct=ret,profit_factor=pf,win_rate_pct=wr,
                   max_drawdown_pct=float(dd.min()*100),num_trades=n,grade=grade)
    weaknesses, suggestions = [], []
    if n<20:
        weaknesses.append("Fewer than 20 trades: insufficient evidence.")
        suggestions.append("Test on more data.")
    if pf<1:
        weaknesses.append("Profit factor below 1 after configured costs.")
        suggestions.append("Review expectancy and costs.")
    if commission==0 and slippage==0:
        weaknesses.append("No costs configured: results may be optimistic.")
        suggestions.append("Set realistic commissions and slippage.")
    return metrics, weaknesses, suggestions, trades_df
