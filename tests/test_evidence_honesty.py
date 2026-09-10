import unittest

from core.evidence_policy import (
    MIN_SCORABLE_TRADES,
    RESEARCH_ENGINE_VERSION,
    evidence_is_sufficient,
    invalidate_stale_research_state,
)
from core.gradecard import build_gradecard
from core.market_fit_analyzer import analyze_market_fit
from core.research_score import calculate_research_score
from core.risk_report import build_risk_report
from core.strategy_doctor import build_strategy_doctor


FIVE_TRADE_RESULT = {
    "profit_factor": 2.98,
    "win_rate_pct": 60.0,
    "max_drawdown_pct": -0.5,
    "total_return_pct": 2.0,
    "num_trades": 5,
}


class EvidenceHonestyTests(unittest.TestCase):
    def test_small_sample_cannot_receive_performance_or_risk_scores(self):
        self.assertFalse(evidence_is_sufficient(FIVE_TRADE_RESULT))
        self.assertEqual("UNSCORED", build_gradecard(FIVE_TRADE_RESULT)["edge_quality"])
        self.assertEqual("UNSCORED", build_gradecard(FIVE_TRADE_RESULT)["overall"])
        self.assertIsNone(calculate_research_score(FIVE_TRADE_RESULT)["score"])
        self.assertIsNone(build_risk_report(FIVE_TRADE_RESULT)["confidence_score"])
        self.assertEqual(
            "UNKNOWN — INSUFFICIENT EVIDENCE",
            build_risk_report(FIVE_TRADE_RESULT)["risk_of_ruin"],
        )
        self.assertEqual("INCONCLUSIVE", build_strategy_doctor(FIVE_TRADE_RESULT)["severity"])

    def test_market_fit_is_not_run_before_baseline_is_scorable(self):
        self.assertEqual([], analyze_market_fit(object(), years=2, baseline_metrics=FIVE_TRADE_RESULT))

    def test_thirty_trades_unlocks_scoring_policy(self):
        metrics = {**FIVE_TRADE_RESULT, "num_trades": MIN_SCORABLE_TRADES}
        self.assertTrue(evidence_is_sufficient(metrics))
        self.assertIsNotNone(calculate_research_score(metrics)["score"])
        self.assertNotEqual("UNSCORED", build_gradecard(metrics)["overall"])

    def test_engine_change_invalidates_generated_research_but_preserves_thesis(self):
        state = {
            "research_engine_version": "older-engine",
            "ai_text": "Trader-authored strategy thesis",
            "blueprint_schema": {"risk": {"capital": 10000}},
            "blueprint_approved": True,
            "approved_strategy_yaml": "old: contract",
            "bt_result": {"metrics": FIVE_TRADE_RESULT},
            "active_workspace_stage": "readiness",
        }

        self.assertTrue(invalidate_stale_research_state(state))
        self.assertEqual(RESEARCH_ENGINE_VERSION, state["research_engine_version"])
        self.assertEqual("Trader-authored strategy thesis", state["ai_text"])
        self.assertEqual("thesis", state["active_workspace_stage"])
        self.assertNotIn("blueprint_schema", state)
        self.assertNotIn("approved_strategy_yaml", state)
        self.assertNotIn("bt_result", state)

        self.assertFalse(invalidate_stale_research_state(state))


if __name__ == "__main__":
    unittest.main()
