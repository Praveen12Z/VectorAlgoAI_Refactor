"""Deterministic regression tests for bar execution and risk controls."""
import pandas as pd
import pytest
from core.backtester_adapter import run_backtest_v2
from core.strategy_config import parse_strategy_yaml

YAML = """
name: execution-test
market: NAS100
timeframe: 1h
indicators: []
entry:
  long:
    - {left: close, op: ">", right: 100}
  short: []
exit:
  long:
    - {type: atr_sl, atr_col: atr14, multiple: 1}
    - {type: atr_tp, atr_col: atr14, multiple: 2}
  short: []
risk:
  capital: 10000
  risk_per_trade_pct: 1
  contract_multiplier: 1
  commission_per_unit_per_side: 0
  slippage_points_per_side: 0
"""

def candles():
    return pd.DataFrame({
        "open": [100, 101, 102, 103],
        "high": [101, 104, 104, 104],
        "low": [99, 95, 101, 102],
        "close": [101, 102, 103, 103],
        "atr14": [2, 2, 2, 2],
    }, index=pd.date_range("2026-01-01", periods=4, freq="h"))

def run(data=None, yaml=YAML):
    return run_backtest_v2(candles() if data is None else data, parse_strategy_yaml(yaml))

def test_next_bar_open_entry():
    _, _, _, trades = run()
    assert trades.iloc[0]["entry_time"] == candles().index[1]
    assert trades.iloc[0]["entry_price"] == 101

def test_intrabar_stop_priority():
    _, _, _, trades = run()
    assert trades.iloc[0]["exit_reason"] == "SL"
    assert trades.iloc[0]["exit_price"] == 99

def test_risk_sizing():
    _, _, _, trades = run()
    assert trades.iloc[0]["quantity"] == pytest.approx(50)
    assert trades.iloc[0]["pnl"] == pytest.approx(-100)

def test_costs_reduce_net_pnl():
    costly = YAML.replace("commission_per_unit_per_side: 0", "commission_per_unit_per_side: 1")
    _, _, _, trades = run(yaml=costly)
    assert trades.iloc[0]["quantity"] < 50
    assert trades.iloc[0]["pnl"] < 0
    assert trades.iloc[0]["fees"] > 0

def test_no_trade_when_no_signal():
    data = candles().copy()
    data["close"] = [100,100,100,100]
    data["high"] = data[["open", "high", "close"]].max(axis=1)
    data["low"] = data[["open", "low", "close"]].min(axis=1)
    _, _, _, trades = run(data)
    assert trades.empty

def test_gap_through_stop_fills_at_open():
    data = candles().copy()
    data.loc[data.index[1], "open"] = 97
    data.loc[data.index[1], "high"] = 98
    data.loc[data.index[1], "close"] = 97
    _, _, _, trades = run(data)
    assert trades.iloc[0]["entry_price"] == 97
    assert trades.iloc[0]["exit_price"] == 95
