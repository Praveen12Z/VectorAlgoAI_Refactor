import unittest

from core.evidence_policy import (
    MIN_SCORABLE_TRADES,
    RESEARCH_ENGINE_VERSION,
    evidence_is_sufficient,
    invalidate_stale_research_state,
)
from core.gradecard import build_gradecard
from core.capital_verdict import get_capital_verdict
from core.market_fit_analyzer import analyze_market_fit
from core.research_score import calculate_research_score
from core.risk_report import build_risk_report
from core.root_cause_analyzer import analyze_root_cause
from core.strategy_doctor import build_strategy_doctor
from core.strategy_optimizer import optimize_strategy


FIVE_TRADE_RESULT = {
    "profit_factor": 2.98,
    "win_rate_pct": 60.0,
    "max_drawdown_pct": -0.5,
    "total_return_pct": 2.0,
    "num_trades": 5,
}

BREAKEVEN_RESULT = {
    "profit_factor": 1.00,
    "win_rate_pct": 40.62,
    "max_drawdown_pct": -6.01,
    "total_return_pct": 0.05,
    "num_trades": 64,
    "risk_sizing_applied": True,
    "costs_included": False,
    "oos_passed": False,
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

    def test_breakeven_baseline_is_consistently_rejected(self):
        research = calculate_research_score(BREAKEVEN_RESULT)
        risk = build_risk_report(BREAKEVEN_RESULT)
        doctor = build_strategy_doctor(BREAKEVEN_RESULT)
        root_cause = analyze_root_cause(BREAKEVEN_RESULT)
        optimizer = optimize_strategy(BREAKEVEN_RESULT)
        gradecard = build_gradecard(BREAKEVEN_RESULT)
        verdict = get_capital_verdict(BREAKEVEN_RESULT)

        self.assertEqual(35, research["score"])
        self.assertEqual("F", research["grade"])
        self.assertEqual("HIGH", risk["risk_of_ruin"])
        self.assertEqual("UNKNOWN — NOT VALIDATED", risk["overfitting_risk"])
        self.assertLessEqual(risk["confidence_score"], 40)
        self.assertEqual("HIGH", doctor["severity"])
        self.assertIn("No baseline edge", doctor["findings"][0])
        self.assertEqual("No Demonstrated Edge", root_cause["main_problem"])
        self.assertEqual("No Demonstrated Edge", optimizer["bottleneck"])
        self.assertEqual("C", gradecard["statistical_validity"])
        self.assertEqual("D", gradecard["risk_management"])
        self.assertEqual("F", gradecard["edge_quality"])
        self.assertEqual("UNVERIFIED", gradecard["robustness"])
        self.assertEqual("F", gradecard["deployability"])
        self.assertEqual("F", gradecard["overall"])
        self.assertEqual("❌ DO NOT DEPLOY — NO DEMONSTRATED EDGE", verdict["verdict"])

    def test_promising_baseline_names_validation_as_the_remaining_problem(self):
        metrics = {
            "profit_factor": 1.33,
            "win_rate_pct": 45.24,
            "max_drawdown_pct": -3.84,
            "total_return_pct": 4.93,
            "num_trades": 42,
            "costs_included": True,
            "oos_passed": False,
            "validation_reason": "The hold-out segment has fewer than 30 trades.",
        }

        self.assertEqual("VALIDATION REQUIRED", build_strategy_doctor(metrics)["severity"])
        self.assertEqual("Robustness Not Verified", analyze_root_cause(metrics)["main_problem"])
        self.assertEqual("Robustness Not Verified", optimize_strategy(metrics)["bottleneck"])
        card = build_gradecard(metrics)
        self.assertEqual("B", card["risk_management"])
        self.assertEqual("UNVERIFIED", card["robustness"])
        self.assertEqual("F", card["deployability"])
        self.assertLessEqual(calculate_research_score(metrics)["score"], 69)
        self.assertEqual(
            "UNDETERMINED — ROBUSTNESS NOT VALIDATED",
            build_risk_report(metrics)["risk_of_ruin"],
        )

    def test_adverse_small_holdout_caps_score_and_does_not_claim_ruin_risk(self):
        metrics = {
            "profit_factor": 1.31,
            "win_rate_pct": 45.24,
            "max_drawdown_pct": -3.83,
            "total_return_pct": 4.50,
            "num_trades": 42,
            "costs_included": True,
            "oos_passed": False,
            "validation_status": "HOLD-OUT ADVERSE — SAMPLE TOO SMALL",
        }

        self.assertEqual(40, calculate_research_score(metrics)["score"])
        self.assertEqual(
            "UNDETERMINED — ROBUSTNESS NOT VALIDATED",
            build_risk_report(metrics)["risk_of_ruin"],
        )

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
