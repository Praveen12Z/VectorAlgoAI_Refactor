import unittest
from types import SimpleNamespace

import pandas as pd

from core.regime_analyzer import analyze_regime_shift


class RegimeAnalyzerTests(unittest.TestCase):
    def test_thresholds_come_from_development_and_holdout_is_descriptive(self):
        index = pd.date_range("2025-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "close": [100.0] * 100,
                "atr14": [1.0] * 70 + [3.0] * 30,
                "ema20": [102.0] * 100,
                "ema50": [100.0] * 100,
            },
            index=index,
        )
        development_trades = pd.DataFrame(
            {
                "entry_time": [index[10], index[20]],
                "pnl": [100.0, -50.0],
                "rr": [2.0, -1.0],
            }
        )
        holdout_trades = pd.DataFrame(
            {
                "entry_time": [index[80], index[90]],
                "pnl": [-50.0, -50.0],
                "rr": [-1.0, -1.0],
            }
        )
        validation = {
            "development": {
                "period": (index[0], index[69], 70),
                "metrics": {"profit_factor": 2.0},
                "trades": development_trades,
            },
            "holdout": {
                "period": (index[70], index[-1], 30),
                "metrics": {"profit_factor": 0.0},
                "trades": holdout_trades,
            },
        }
        cfg = SimpleNamespace(
            indicators=[
                SimpleNamespace(name="atr14", type="atr", period=14),
                SimpleNamespace(name="ema20", type="ema", period=20),
                SimpleNamespace(name="ema50", type="ema", period=50),
            ]
        )

        result = analyze_regime_shift(data, cfg, validation)

        self.assertEqual("DESCRIPTIVE — NOT CAUSAL", result["status"])
        self.assertEqual(0.0, result["development_context"]["high_volatility_share_pct"])
        self.assertEqual(100.0, result["holdout_context"]["high_volatility_share_pct"])
        self.assertEqual(4, sum(row["trades"] for row in result["trade_regimes"]))
        self.assertTrue(any("not proof of cause" in item for item in result["observations"]))


if __name__ == "__main__":
    unittest.main()
