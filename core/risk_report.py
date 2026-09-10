# core/risk_report.py

from core.evidence_policy import (
    baseline_edge_is_demonstrated,
    evidence_is_sufficient,
    robustness_is_verified,
)

def build_risk_report(metrics: dict) -> dict:

    pf = float(metrics.get("profit_factor", 0))
    dd = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))

    if not evidence_is_sufficient(metrics):
        return {
            "risk_of_ruin": "UNKNOWN — INSUFFICIENT EVIDENCE",
            "overfitting_risk": "HIGH",
            "confidence_score": None,
        }

    # ----------------------------------
    # Risk Of Ruin
    # ----------------------------------

    if not baseline_edge_is_demonstrated(metrics):
        risk_of_ruin = "HIGH"
    elif pf >= 1.5 and dd < 10:
        risk_of_ruin = "LOW"

    elif pf >= 1.1 and dd < 20:
        risk_of_ruin = "MEDIUM"

    else:
        risk_of_ruin = "HIGH"

    # ----------------------------------
    # Overfitting Risk
    # ----------------------------------

    if not robustness_is_verified(metrics):
        overfitting = "UNKNOWN — NOT VALIDATED"
    elif trades < 100:
        overfitting = "MEDIUM"
    else:
        overfitting = "LOW"

    # ----------------------------------
    # Sample Confidence
    # ----------------------------------

    if trades >= 200:
        confidence = 70
    elif trades >= 100:
        confidence = 55
    else:
        confidence = 40

    if metrics.get("costs_included"):
        confidence += 15
    if metrics.get("oos_passed"):
        confidence += 15
    if not baseline_edge_is_demonstrated(metrics):
        confidence = min(confidence, 40)

    return {
        "risk_of_ruin": risk_of_ruin,
        "overfitting_risk": overfitting,
        "confidence_score": confidence,
    }
