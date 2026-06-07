# core/risk_report.py

def build_risk_report(metrics: dict) -> dict:

    pf = float(metrics.get("profit_factor", 0))
    dd = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))

    # ----------------------------------
    # Risk Of Ruin
    # ----------------------------------

    if pf >= 1.5 and dd < 10:
        risk_of_ruin = "LOW"

    elif pf >= 1.1 and dd < 20:
        risk_of_ruin = "MEDIUM"

    else:
        risk_of_ruin = "HIGH"

    # ----------------------------------
    # Overfitting Risk
    # ----------------------------------

    if trades < 20:
        overfitting = "HIGH"

    elif trades < 50:
        overfitting = "MEDIUM"

    else:
        overfitting = "LOW"

    # ----------------------------------
    # Sample Confidence
    # ----------------------------------

    if trades >= 200:
        confidence = 90

    elif trades >= 100:
        confidence = 75

    elif trades >= 50:
        confidence = 60

    elif trades >= 20:
        confidence = 40

    else:
        confidence = 20

    return {
        "risk_of_ruin": risk_of_ruin,
        "overfitting_risk": overfitting,
        "confidence_score": confidence,
    }