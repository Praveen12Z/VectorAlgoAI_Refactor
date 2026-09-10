import unittest

import yaml

from core.ai_strategy_builder import build_strategy_from_text
from core.schema_to_yaml_compiler import compile_schema_to_yaml


class StrategyInterpretationTests(unittest.TestCase):
    def test_explicit_parameters_survive_into_machine_contract(self):
        thesis = (
            "Trade NAS100 EMA20 above EMA50 and EMA200 pullbacks. "
            "Require RSI14 above 60. Use ATR14 with a 1.5 ATR stop, "
            "target 2R, risk 0.5%, account €25,000."
        )

        schema = build_strategy_from_text(thesis)
        contract = yaml.safe_load(compile_schema_to_yaml(schema, "NAS100", "1h"))

        self.assertEqual([20, 50, 200], [i["period"] for i in contract["indicators"] if i["type"] == "ema"])
        self.assertIn({"left": "rsi14", "op": ">", "right": 60.0}, contract["entry"]["long"])
        self.assertIn({"type": "atr_sl", "atr_col": "atr14", "multiple": 1.5}, contract["exit"]["long"])
        self.assertIn({"type": "atr_tp", "atr_col": "atr14", "multiple": 3.0}, contract["exit"]["long"])
        self.assertEqual(0.5, contract["risk"]["risk_per_trade_pct"])
        self.assertEqual(25000.0, contract["risk"]["capital"])
        self.assertEqual([], contract["interpretation"]["assumptions"])

    def test_vague_parameters_are_disclosed_as_assumptions(self):
        schema = build_strategy_from_text(
            "Trade EMA pullbacks with RSI confirmation, an ATR stop and a target."
        )

        fields = {item["field"] for item in schema["assumptions"]}
        self.assertTrue({
            "EMA periods",
            "RSI period",
            "RSI threshold",
            "ATR period",
            "Stop distance",
            "Profit target",
            "Risk per trade",
            "Research capital",
        }.issubset(fields))

    def test_capital_is_preserved_in_natural_account_phrasings(self):
        phrasings = (
            "risk 0.5% of a €25,000 account",
            "risk 0.5%, account €25,000",
            "risk 0.5% on a $25,000 trading account",
            "risk 0.5%, capital 25000",
        )
        for phrase in phrasings:
            with self.subTest(phrase=phrase):
                schema = build_strategy_from_text(
                    f"Trade EMA20 pullbacks with an ATR14 stop, target 2R, {phrase}."
                )
                self.assertEqual(25000.0, schema["risk"]["capital"])
                self.assertNotIn(
                    "Research capital",
                    {item["field"] for item in schema["assumptions"]},
                )

    def test_rsi_below_is_not_rewritten_as_above(self):
        schema = build_strategy_from_text("Enter at support when RSI 9 below 30, risk 1%.")
        contract = yaml.safe_load(compile_schema_to_yaml(schema, "XAUUSD", "15m"))

        self.assertIn({"left": "rsi9", "op": "<", "right": 30.0}, contract["entry"]["long"])


if __name__ == "__main__":
    unittest.main()
