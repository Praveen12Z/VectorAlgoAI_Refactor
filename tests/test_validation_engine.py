import unittest
from unittest.mock import patch

import pandas as pd

from core.backtester_adapter import ExecutionCostModel
from core.validation_engine import run_chronological_validation


class ValidationEngineTests(unittest.TestCase):
    def setUp(self):
        self.data = pd.DataFrame(
            {"close": range(100)},
            index=pd.date_range("2025-01-01", periods=100, freq="D"),
        )
        self.costs = ExecutionCostModel(
            spread_points=1.0,
            slippage_points_per_side=0.5,
        )

    @staticmethod
    def _result(pf, trades):
        metrics = {
            "profit_factor": pf,
            "total_return_pct": 5.0,
            "max_drawdown_pct": -5.0,
            "win_rate_pct": 50.0,
            "num_trades": trades,
            "costs_included": True,
            "oos_passed": False,
        }
        return metrics, [], [], pd.DataFrame()

    def test_pass_requires_edge_in_both_chronological_segments(self):
        responses = [
            self._result(1.45, 80),
            self._result(1.40, 45),
            self._result(1.20, 35),
        ]
        with patch("core.validation_engine.run_backtest_v2", side_effect=responses):
            result = run_chronological_validation(
                self.data, object(), self.costs, holdout_pct=30
            )

        self.assertTrue(result["passed"])
        self.assertEqual("HOLD-OUT PASSED", result["status"])
        self.assertEqual(70, result["development"]["period"][2])
        self.assertEqual(30, result["holdout"]["period"][2])
        self.assertTrue(result["full"]["metrics"]["oos_passed"])

    def test_small_holdout_cannot_pass(self):
        responses = [
            self._result(1.40, 42),
            self._result(1.35, 30),
            self._result(1.30, 12),
        ]
        with patch("core.validation_engine.run_backtest_v2", side_effect=responses):
            result = run_chronological_validation(
                self.data, object(), self.costs, holdout_pct=30
            )

        self.assertFalse(result["passed"])
        self.assertEqual("INSUFFICIENT HOLD-OUT EVIDENCE", result["status"])
        self.assertIn("12", result["reason"])
        self.assertFalse(result["full"]["metrics"]["oos_passed"])


if __name__ == "__main__":
    unittest.main()
