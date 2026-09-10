import json
import unittest
from types import SimpleNamespace

import pandas as pd

from core.research_record import build_research_record


class ResearchRecordTests(unittest.TestCase):
    def test_record_is_deterministic_immutable_and_json_safe(self):
        contract = {
            "strategy_contract": {
                "version": "1.1",
                "machine_fingerprint": "machine-hash",
                "rules_fingerprint": "rules-hash",
                "source": {"original_text": "Trade the approved rules."},
            }
        }
        trades = pd.DataFrame(
            {
                "entry_time": [pd.Timestamp("2026-01-01", tz="UTC")],
                "pnl": [100.0],
                "rr": [float("inf")],
            }
        )
        validation = {
            "full": {
                "period": (pd.Timestamp("2025-01-01"), pd.Timestamp("2026-01-01"), 100),
                "metrics": {"profit_factor": 1.3},
                "trades": trades,
            },
            "development": {"metrics": {"profit_factor": 1.5}},
            "holdout": {"metrics": {"profit_factor": 1.1}},
            "status": "HOLD-OUT PASSED",
            "passed": True,
            "holdout_pct": 30,
            "cost_model": {"spread_points": 1.0},
            "regime_analysis": {"status": "DESCRIPTIVE — NOT CAUSAL"},
        }
        cfg = SimpleNamespace(name="Version B", market="NAS100", timeframe="1h")

        first = build_research_record(
            strategy_name="Version B",
            strategy_yaml="name: Version B",
            contract=contract,
            cfg=cfg,
            validation=validation,
        )
        second = build_research_record(
            strategy_name="Version B",
            strategy_yaml="name: Version B",
            contract=contract,
            cfg=cfg,
            validation=validation,
        )

        self.assertEqual(first["record_hash"], second["record_hash"])
        self.assertEqual("machine-hash", first["contract_fingerprint"])
        self.assertIsNone(first["trade_records"][0]["rr"])
        json.dumps(first, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
