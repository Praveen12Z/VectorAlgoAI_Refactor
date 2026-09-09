import unittest

import yaml

from core.ai_strategy_builder import build_strategy_from_text
from core.research_contract import strategy_contract_issues
from core.schema_to_yaml_compiler import compile_schema_to_yaml
from core.strategy_config import parse_strategy_yaml
from core.strategy_contract import (
    CONTRACT_VERSION,
    approve_strategy_contract,
    contract_gate_issues,
    require_approved_strategy_contract,
)


SUPPORTED_THESIS = (
    "Trade EMA20 above EMA50 pullbacks with RSI14 above 60. "
    "Use ATR14 with a 1.5 ATR stop, target 2R, risk 0.5%, account €25,000."
)


class StrategyContractTests(unittest.TestCase):
    def _compile(self, thesis=SUPPORTED_THESIS):
        schema = build_strategy_from_text(thesis)
        strategy = yaml.safe_load(compile_schema_to_yaml(schema, "NAS100", "1h"))
        return schema, strategy

    def test_contract_v1_records_every_interpreted_rule_and_capability(self):
        schema, strategy = self._compile()
        contract = strategy["strategy_contract"]

        self.assertEqual(CONTRACT_VERSION, contract["version"])
        self.assertEqual(len(schema["components"]) + 1, len(contract["rules"]))
        self.assertEqual([], contract_gate_issues(strategy, require_approval=False))
        self.assertTrue(all(rule["status"] == "executable" for rule in contract["rules"]))
        self.assertEqual("draft", contract["approval"]["state"])

    def test_approved_contract_is_required_before_backtest_parsing(self):
        _, strategy = self._compile()

        with self.assertRaisesRegex(ValueError, "has not been approved"):
            require_approved_strategy_contract(strategy)

        approved = approve_strategy_contract(strategy, assumptions_accepted=True)
        require_approved_strategy_contract(approved)
        config = parse_strategy_yaml(yaml.safe_dump(approved, sort_keys=False))
        self.assertEqual("NAS100", config.market)
        self.assertEqual("approved", config.raw["strategy_contract"]["approval"]["state"])

    def test_unsupported_news_rule_blocks_approval(self):
        _, strategy = self._compile(SUPPORTED_THESIS + " Avoid high-impact news.")
        issues = strategy_contract_issues(strategy)

        self.assertTrue(any("News Filter is unsupported" in issue for issue in issues))
        with self.assertRaisesRegex(ValueError, "cannot be approved"):
            approve_strategy_contract(strategy, assumptions_accepted=True)

    def test_manual_support_resistance_is_not_silently_compiled(self):
        _, strategy = self._compile(
            "Buy a pullback at support with RSI14 above 55. Use ATR14 with a 2 ATR stop, "
            "target 2R, risk 1%, account €10,000."
        )

        serialized_entries = yaml.safe_dump(strategy["entry"])
        self.assertNotIn("support_zone", serialized_entries)
        self.assertTrue(any(
            rule["component"] == "support_resistance" and rule["status"] == "manual"
            for rule in strategy["strategy_contract"]["rules"]
        ))

    def test_machine_change_after_approval_invalidates_contract(self):
        _, strategy = self._compile()
        approved = approve_strategy_contract(strategy, assumptions_accepted=True)
        approved["risk"]["risk_per_trade_pct"] = 5.0

        with self.assertRaisesRegex(ValueError, "executable YAML changed"):
            require_approved_strategy_contract(approved)

    def test_rule_status_change_after_approval_invalidates_contract(self):
        _, strategy = self._compile()
        approved = approve_strategy_contract(strategy, assumptions_accepted=True)
        approved["strategy_contract"]["rules"][0]["status"] = "manual"

        with self.assertRaisesRegex(ValueError, "contract rules changed"):
            require_approved_strategy_contract(approved)


if __name__ == "__main__":
    unittest.main()
