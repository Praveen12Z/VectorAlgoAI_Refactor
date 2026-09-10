import unittest

import pandas as pd

from core.backtester_adapter import ExecutionCostModel, run_backtest_v2
from core.capital_verdict import get_capital_verdict
from core.strategy_config import parse_strategy_yaml


BLUEPRINT = """
name: Execution contract test
market: NAS100
timeframe: 1h
indicators:
  - name: atr
    type: atr
    period: 1
entry:
  long:
    - left: close
      op: ">"
      right: 99
  short: []
exit:
  long:
    - type: atr_sl
      atr_col: atr
      multiple: 1
    - type: atr_tp
      atr_col: atr
      multiple: 2
  short: []
risk:
  capital: 10000
  risk_per_trade_pct: 1
  point_value: 1
"""


class ExecutionContractTests(unittest.TestCase):
    def _run(self, second_high, second_low):
        index = pd.date_range("2026-01-01", periods=2, freq="h")
        data = pd.DataFrame(
            {
                "open": [100.0, 100.0],
                "high": [101.0, second_high],
                "low": [99.0, second_low],
                "close": [100.0, 100.0],
                "atr": [10.0, 10.0],
            },
            index=index,
        )
        return run_backtest_v2(data, parse_strategy_yaml(BLUEPRINT))

    def test_stop_wins_when_stop_and_target_are_inside_same_candle(self):
        metrics, _, _, trades = self._run(second_high=121.0, second_low=89.0)

        self.assertEqual(trades.iloc[0]["exit_reason"], "SL")
        self.assertEqual(trades.iloc[0]["exit_price"], 90.0)
        self.assertAlmostEqual(trades.iloc[0]["size"], 10.0)
        self.assertAlmostEqual(trades.iloc[0]["pnl"], -100.0)
        self.assertAlmostEqual(trades.iloc[0]["rr"], -1.0)
        self.assertAlmostEqual(metrics["total_return_pct"], -1.0)

    def test_target_uses_risk_sized_cash_pnl(self):
        metrics, _, _, trades = self._run(second_high=121.0, second_low=95.0)

        self.assertEqual(trades.iloc[0]["exit_reason"], "TP")
        self.assertEqual(trades.iloc[0]["exit_price"], 120.0)
        self.assertAlmostEqual(trades.iloc[0]["pnl"], 200.0)
        self.assertAlmostEqual(trades.iloc[0]["rr"], 2.0)
        self.assertAlmostEqual(metrics["total_return_pct"], 2.0)

    def test_explicit_costs_reduce_size_and_net_pnl(self):
        index = pd.date_range("2026-01-01", periods=2, freq="h")
        data = pd.DataFrame(
            {
                "open": [100.0, 100.0],
                "high": [101.0, 121.0],
                "low": [99.0, 95.0],
                "close": [100.0, 100.0],
                "atr": [10.0, 10.0],
            },
            index=index,
        )
        costs = ExecutionCostModel(spread_points=1.0, slippage_points_per_side=0.5)
        metrics, _, _, trades = run_backtest_v2(
            data, parse_strategy_yaml(BLUEPRINT), costs
        )

        self.assertAlmostEqual(trades.iloc[0]["size"], 100 / 12)
        self.assertAlmostEqual(trades.iloc[0]["gross_pnl"], 2000 / 12)
        self.assertAlmostEqual(trades.iloc[0]["trading_cost"], 200 / 12)
        self.assertAlmostEqual(trades.iloc[0]["pnl"], 150.0)
        self.assertAlmostEqual(metrics["total_return_pct"], 1.5)
        self.assertTrue(metrics["costs_included"])

    def test_capital_verdict_refuses_unverified_backtest(self):
        verdict = get_capital_verdict(
            {
                "profit_factor": 2.0,
                "total_return_pct": 20.0,
                "max_drawdown_pct": -8.0,
                "num_trades": 100,
                "win_rate_pct": 60.0,
                "costs_included": False,
                "oos_passed": False,
            }
        )

        self.assertEqual(verdict["verdict"], "⚠ RESEARCH ONLY — ROBUSTNESS NOT VERIFIED")
        self.assertFalse(verdict["capital_approved"])


if __name__ == "__main__":
    unittest.main()
