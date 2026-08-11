import unittest

import pandas as pd

from core.rules import evaluate_rule_group
from core.signal_engine import generate_signals


class PipelineContractTests(unittest.TestCase):
    def setUp(self):
        self.price_data = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.0, 101.0, 102.0],
            }
        )

    def test_legacy_signal_engine_uses_the_canonical_rule_engine(self):
        config = {
            "indicators": [],
            "entry_rules": [{"all": [{"left": "close", "op": ">", "right": 100.0}]}],
            "exit_rules": [{"all": [{"left": "close", "op": ">=", "right": 102.0}]}],
        }

        result = generate_signals(self.price_data, config)

        self.assertEqual(result["entry_signal"].tolist(), [0, 1, 1])
        self.assertEqual(result["exit_signal"].tolist(), [0, 0, 1])
        self.assertEqual(result["position"].tolist(), [0, 1, 1])

    def test_rule_group_contract(self):
        matched = evaluate_rule_group(
            self.price_data,
            1,
            {"all": [{"left": "close", "op": ">", "right": 100.0}]},
        )
        self.assertTrue(matched)


if __name__ == "__main__":
    unittest.main()
