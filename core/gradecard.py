# core/gradecard.py

import math

from core.evidence_policy import (
    baseline_edge_is_demonstrated,
    evidence_is_sufficient,
    robustness_is_verified,
)


def _safe_float(value, default=0.0):
    try:
        x = float(value)
        if math.isnan(x):
            return default
        if math.isinf(x):
            return 999.0 if x > 0 else -999.0
        return x
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def build_gradecard(metrics: dict) -> dict:
    """
    Institutional-readiness gradecard for strategy evaluation.

    Grades:
      A = strong
      B = acceptable
      C = weak / needs improvement
      D = poor
      F = not deployable
    """
    if not evidence_is_sufficient(metrics):
        return {
            "statistical_validity": "UNSCORED",
            "risk_management": "UNSCORED",
            "edge_quality": "UNSCORED",
            "robustness": "UNSCORED",
            "deployability": "UNSCORED",
            "overall": "UNSCORED",
        }

    pf = _safe_float(metrics.get("profit_factor", 0))
    win_rate = _safe_float(metrics.get("win_rate_pct", 0))
    drawdown = abs(_safe_float(metrics.get("max_drawdown_pct", 0)))
    trades = _safe_int(metrics.get("num_trades", 0))
    total_return = _safe_float(metrics.get("total_return_pct", 0))

    # Statistical validity
    if trades >= 250:
        statistical = "A"
    elif trades >= 100:
        statistical = "B"
    elif trades >= 50:
        statistical = "C"
    elif trades >= 30:
        statistical = "D"
    else:
        statistical = "F"

    # Risk management
    if pf < 1.10:
        risk = "D"
    elif drawdown <= 8:
        risk = "A"
    elif drawdown <= 15:
        risk = "B"
    elif drawdown <= 25:
        risk = "C"
    elif drawdown <= 35:
        risk = "D"
    else:
        risk = "F"

    # Edge quality
    if not baseline_edge_is_demonstrated(metrics):
        edge = "F"
    elif pf >= 1.6:
        edge = "A"
    elif pf >= 1.4:
        edge = "B"
    elif pf >= 1.2:
        edge = "C"
    elif pf >= 1.1:
        edge = "D"
    else:
        edge = "F"

    # Robustness is never inferred from in-sample trade count. It must be
    # earned through cost-aware and out-of-sample validation.
    if not robustness_is_verified(metrics):
        robustness = "UNVERIFIED"
    elif trades >= 250 and pf >= 1.4:
        robustness = "A"
    elif trades >= 100 and pf >= 1.3:
        robustness = "B"
    elif trades >= 50 and pf >= 1.2:
        robustness = "C"
    elif trades >= 30 and pf >= 1.1:
        robustness = "D"
    else:
        robustness = "F"

    # Deployability
    if not baseline_edge_is_demonstrated(metrics) or not robustness_is_verified(metrics):
        deployability = "F"
    elif trades >= 100 and pf >= 1.4 and drawdown <= 15:
        deployability = "A"
    elif trades >= 50 and pf >= 1.3 and drawdown <= 20:
        deployability = "B"
    elif trades >= 30 and pf >= 1.2:
        deployability = "C"
    elif trades >= 30:
        deployability = "D"
    else:
        deployability = "F"

    grades = [statistical, risk, edge, deployability]
    score_map = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 0}
    avg = sum(score_map[g] for g in grades) / len(grades)

    if edge == "F" or deployability == "F":
        overall = "F"
    elif avg >= 4.5:
        overall = "A"
    elif avg >= 3.5:
        overall = "B"
    elif avg >= 2.5:
        overall = "C"
    elif avg >= 1.5:
        overall = "D"
    else:
        overall = "F"

    return {
        "statistical_validity": statistical,
        "risk_management": risk,
        "edge_quality": edge,
        "robustness": robustness,
        "deployability": deployability,
        "overall": overall,
    }
