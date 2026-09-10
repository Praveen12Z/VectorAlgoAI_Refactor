"""Chronological hold-out validation for an approved strategy contract."""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.backtester_adapter import ExecutionCostModel, run_backtest_v2
from core.evidence_policy import MIN_SCORABLE_TRADES, baseline_edge_is_demonstrated


MIN_ADVERSE_HOLDOUT_TRADES = 10


def _period(df: pd.DataFrame) -> tuple[Any, Any, int]:
    if df.empty:
        return None, None, 0
    return df.index[0], df.index[-1], len(df)


def _comparison_status(development: dict, holdout: dict, costs_included: bool) -> dict:
    development_trades = int(development.get("num_trades", 0))
    holdout_trades = int(holdout.get("num_trades", 0))

    if not costs_included:
        return {
            "status": "COSTS REQUIRED",
            "passed": False,
            "reason": "At least one non-zero execution-cost assumption is required.",
        }
    holdout_pf = float(holdout.get("profit_factor", 0))
    holdout_return = float(holdout.get("total_return_pct", 0))
    if (
        holdout_trades >= MIN_ADVERSE_HOLDOUT_TRADES
        and holdout_trades < MIN_SCORABLE_TRADES
        and (holdout_pf < 0.80 or holdout_return < 0)
    ):
        return {
            "status": "HOLD-OUT ADVERSE — SAMPLE TOO SMALL",
            "passed": False,
            "reason": (
                f"Hold-out produced only {holdout_trades} trades, so the result is not "
                f"conclusive; however PF {holdout_pf:.2f} and return {holdout_return:.2f}% "
                "are materially adverse and prohibit deployment."
            ),
        }
    if development_trades < MIN_SCORABLE_TRADES or holdout_trades < MIN_SCORABLE_TRADES:
        return {
            "status": "INSUFFICIENT HOLD-OUT EVIDENCE",
            "passed": False,
            "reason": (
                f"Development produced {development_trades} trades and hold-out produced "
                f"{holdout_trades}; each segment requires at least {MIN_SCORABLE_TRADES}."
            ),
        }
    if not baseline_edge_is_demonstrated(development):
        return {
            "status": "DEVELOPMENT EDGE FAILED",
            "passed": False,
            "reason": "The cost-aware development segment has no demonstrated edge.",
        }
    if not baseline_edge_is_demonstrated(holdout):
        return {
            "status": "HOLD-OUT EDGE FAILED",
            "passed": False,
            "reason": "The unchanged rules did not retain a demonstrated edge on hold-out data.",
        }

    development_pf = float(development.get("profit_factor", 0))
    retention = holdout_pf / development_pf if development_pf > 0 else 0.0
    holdout_drawdown = abs(float(holdout.get("max_drawdown_pct", 0)))
    if retention < 0.70:
        return {
            "status": "HOLD-OUT DEGRADATION",
            "passed": False,
            "reason": f"Hold-out profit factor retained only {retention:.0%} of development performance.",
        }
    if holdout_drawdown > 25:
        return {
            "status": "HOLD-OUT RISK FAILED",
            "passed": False,
            "reason": f"Hold-out drawdown reached {holdout_drawdown:.2f}%.",
        }
    return {
        "status": "HOLD-OUT PASSED",
        "passed": True,
        "reason": "The unchanged, cost-aware rules retained positive evidence on the hold-out segment.",
    }


def run_chronological_validation(
    df: pd.DataFrame,
    cfg,
    cost_model: ExecutionCostModel,
    holdout_pct: int = 30,
) -> dict:
    """Run full, development and hold-out tests with identical rules and costs."""
    if df is None or df.empty:
        raise ValueError("Validation requires a non-empty historical dataset.")
    if not 20 <= int(holdout_pct) <= 40:
        raise ValueError("Hold-out percentage must be between 20 and 40.")

    split_index = int(len(df) * (1 - int(holdout_pct) / 100.0))
    if split_index <= 0 or split_index >= len(df):
        raise ValueError("The selected historical window cannot be split into validation segments.")

    development_df = df.iloc[:split_index].copy()
    holdout_df = df.iloc[split_index:].copy()

    full_metrics, weaknesses, suggestions, trades = run_backtest_v2(df, cfg, cost_model)
    development_metrics, _, _, development_trades = run_backtest_v2(
        development_df, cfg, cost_model
    )
    holdout_metrics, _, _, holdout_trades = run_backtest_v2(holdout_df, cfg, cost_model)
    outcome = _comparison_status(
        development_metrics,
        holdout_metrics,
        bool(full_metrics.get("costs_included")),
    )

    full_metrics["oos_passed"] = bool(outcome["passed"])
    full_metrics["validation_status"] = outcome["status"]
    full_metrics["validation_reason"] = outcome["reason"]
    full_metrics["holdout_pct"] = int(holdout_pct)

    if not outcome["passed"]:
        weaknesses = list(weaknesses)
        suggestions = list(suggestions)
        weaknesses.append(f"Validation incomplete: {outcome['reason']}")
        suggestions.append(
            "Keep the rules frozen and obtain sufficient hold-out evidence before deployment."
        )

    return {
        "full": {
            "metrics": full_metrics,
            "trades": trades,
            "period": _period(df),
            "weaknesses": weaknesses,
            "suggestions": suggestions,
        },
        "development": {
            "metrics": development_metrics,
            "trades": development_trades,
            "period": _period(development_df),
        },
        "holdout": {
            "metrics": holdout_metrics,
            "trades": holdout_trades,
            "period": _period(holdout_df),
        },
        "status": outcome["status"],
        "passed": outcome["passed"],
        "reason": outcome["reason"],
        "holdout_pct": int(holdout_pct),
        "cost_model": cost_model.as_dict(),
    }
