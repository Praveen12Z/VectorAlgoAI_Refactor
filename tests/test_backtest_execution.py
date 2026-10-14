"""Regression tests documenting execution defects in the current backtester.

Run: python -m pytest tests/test_backtest_execution.py
"""
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
"""


def candles():
    return pd.DataFrame({
        "open": [100, 101, 102, 103],
        "high": [101, 104, 104, 104],
        "low": [99, 95, 101, 102],
        "close": [101, 102, 103, 103],
        "atr14": [2, 2, 2, 2],
    }, index=pd.date_range("2026-01-01", periods=4, freq="h"))


@pytest.mark.xfail(strict=True, reason="Current engine enters at signal-bar close")
def test_signal_executes_at_next_bar_open():
    _, _, _, trades = run_backtest_v2(candles(), parse_strategy_yaml(YAML))
    assert trades.iloc[0]["entry_time"] == candles().index[1]
    assert trades.iloc[0]["entry_price"] == 101


@pytest.mark.xfail(strict=True, reason="Current engine ignores intrabar stop touches")
def test_intrabar_stop_has_priority_when_stop_and_target_touched():
    _, _, _, trades = run_backtest_v2(candles(), parse_strategy_yaml(YAML))
    assert trades.iloc[0]["exit_reason"] == "SL"


@pytest.mark.xfail(strict=True, reason="Current engine does not implement risk sizing")
def test_trade_output_contains_risk_sized_quantity():
    _, _, _, trades = run_backtest_v2(candles(), parse_strategy_yaml(YAML))
    assert "quantity" in trades.columns
    assert trades.iloc[0]["quantity"] > 0
