# core/strategy_doctor.py

import math

from core.evidence_policy import MIN_SCORABLE_TRADES, evidence_is_sufficient


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


def build_strategy_doctor(metrics: dict) -> dict:
    pf = _safe_float(metrics.get("profit_factor", 0))
    wr = _safe_float(metrics.get("win_rate_pct", 0))
    dd = abs(_safe_float(metrics.get("max_drawdown_pct", 0)))
    try:
        trades = int(metrics.get("num_trades", 0))
    except Exception:
        trades = 0
    total_return = _safe_float(metrics.get("total_return_pct", 0))

    if not evidence_is_sufficient(metrics):
        return {
            "severity": "INCONCLUSIVE",
            "findings": [
                f"Only {trades} trade(s) were observed. Performance, edge and risk cannot be scored reliably."
            ],
            "recommendations": [
                f"Collect at least {MIN_SCORABLE_TRADES} trades before evaluating performance or deployment."
            ],
        }

    findings = []
    recommendations = []
    severity = "LOW"

    if trades < 10:
        severity = "CRITICAL"
        findings.append(f"Only {trades} trade(s) detected. Statistical evidence is invalid.")
        recommendations.append("Collect at least 30 trades before considering deployment.")
    elif trades < 30:
        severity = "HIGH"
        findings.append(f"Only {trades} trades detected. Sample size remains weak.")
        recommendations.append("Expand test period or increase signal frequency.")

    if pf < 0.90:
        severity = "CRITICAL"
        findings.append("Strategy has strongly negative expectancy (Profit Factor < 0.90).")
        recommendations.append("Strategy is structurally unprofitable. Rebuild logic.")
    elif pf < 1.00:
        if severity == "LOW":
            severity = "HIGH"
        findings.append("Strategy has negative expectancy (Profit Factor < 1.00).")
        recommendations.append("Rework entry conditions and risk management.")
    elif pf < 1.10:
        severity = "HIGH"
        findings.append("No baseline edge is demonstrated (Profit Factor < 1.10).")
        recommendations.append("Do not deploy. Test one change at a time against this baseline.")
    elif pf < 1.20:
        findings.append("The observed edge is fragile.")
        recommendations.append("Challenge the edge with realistic costs and hold-out data.")

    if dd > 25:
        if severity == "LOW":
            severity = "HIGH"
        findings.append(f"Drawdown is high ({dd:.2f}%).")
        recommendations.append("Reduce risk per trade or tighten exits.")

    if wr < 40:
        findings.append(f"Low win rate ({wr:.1f}%).")
        recommendations.append("Improve signal quality.")

    if total_return < -10:
        severity = "CRITICAL"
        findings.append(f"Strategy lost {abs(total_return):.2f}%.")
        recommendations.append("Immediate redesign required.")
    elif total_return <= 0:
        if severity == "LOW":
            severity = "HIGH"
        findings.append("Strategy failed to generate positive return.")
        recommendations.append("Do not deploy. Rebuild logic.")
    elif total_return > 0 and trades <= 5:
        findings.append("Positive return achieved with insufficient evidence.")
        recommendations.append("Result may be luck. Gather more samples.")

    if not metrics.get("costs_included"):
        findings.append("Trading costs are not included, so net expectancy is unknown.")
        recommendations.append("Add spread, commission and slippage before judging profitability.")
    if not metrics.get("oos_passed"):
        findings.append("No hold-out or out-of-sample validation has passed.")
        recommendations.append("Reserve unseen data and validate without retuning the rules.")

    if not findings:
        findings.append("No major structural weaknesses detected.")
    if not recommendations:
        recommendations.append("Continue out-of-sample testing.")

    # De-duplicate while preserving order
    findings = list(dict.fromkeys(findings))
    recommendations = list(dict.fromkeys(recommendations))

    return {
        "severity": severity,
        "findings": findings,
        "recommendations": recommendations,
    }
