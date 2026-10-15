"""Causal support/resistance and MNQ execution tests."""
import pandas as pd
import pytest
from core.support_resistance import add_support_resistance
from core.backtester_adapter import run_backtest_v2
from core.strategy_config import parse_strategy_yaml


def test_levels_exclude_current_candle():
    data = pd.DataFrame({
        "open": [100, 101, 102, 103],
        "high": [102, 103, 104, 120],
        "low": [98, 99, 100, 101],
        "close": [101, 102, 103, 119],
    })
    out = add_support_resistance(data, lookback=3)
    assert out.loc[3, "resistance"] == 104
    assert out.loc[3, "support"] == 98
    assert bool(out.loc[3, "sr_breakout_long"])


def test_levels_are_causal_when_future_data_changes():
    data = pd.DataFrame({
        "open": [100, 101, 102, 103, 104],
        "high": [102, 103, 104, 105, 106],
        "low": [98, 99, 100, 101, 102],
        "close": [101, 102, 103, 104, 105],
    })
    first = add_support_resistance(data, lookback=2)
    modified = data.copy()
    modified.loc[4, "high"] = 1000
    modified.loc[4, "close"] = 999
    second = add_support_resistance(modified, lookback=2)
    pd.testing.assert_series_equal(first["resistance"].iloc[:5], second["resistance"].iloc[:5])


def test_mnq_two_dollars_per_point_and_integer_quantity():
    yaml = """
name: MNQ-test
market: MNQ
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
  contract_multiplier: 2
  integer_units: true
  commission_per_unit_per_side: 0
  slippage_points_per_side: 0
"""
    bars = pd.DataFrame({
        "open": [100, 101, 102],
        "high": [101, 102, 103],
        "low": [99, 98, 101],
        "close": [101, 100, 102],
        "atr14": [2, 2, 2],
    }, index=pd.date_range("2026-01-01", periods=3, freq="h"))
    _, _, _, trades = run_backtest_v2(bars, parse_strategy_yaml(yaml))
    assert trades.iloc[0]["quantity"] == 25
    assert trades.iloc[0]["pnl"] == pytest.approx(-100)
