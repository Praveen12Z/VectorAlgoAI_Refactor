# core/capital_verdict.py

def get_capital_verdict(metrics: dict) -> dict:

    pf = float(metrics.get("profit_factor", 0))
    dd = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))
    wr = float(metrics.get("win_rate_pct", 0))

    # ------------------------------
    # Verdict
    # ------------------------------

    if trades < 30:
        verdict = "⚠ INSUFFICIENT DATA"
        color = "orange"

    elif pf < 1.10 or float(metrics.get("total_return_pct", 0)) <= 0:
        verdict = "❌ DO NOT DEPLOY — NO DEMONSTRATED EDGE"
        color = "red"

    elif not metrics.get("costs_included") or not metrics.get("oos_passed"):
        verdict = "⚠ RESEARCH ONLY — ROBUSTNESS NOT VERIFIED"
        color = "orange"

    elif dd > 25:
        verdict = "❌ DO NOT DEPLOY"
        color = "red"

    elif pf > 1.6 and wr > 50 and dd < 15:
        verdict = "✅ ELIGIBLE FOR CONTROLLED PAPER TEST"
        color = "green"

    elif pf > 1.3 and wr > 45:
        verdict = "⚠ PAPER TEST WITH RESTRICTED RISK"
        color = "orange"

    else:
        verdict = "⚠ NEEDS MORE TESTING"
        color = "orange"

    return {
        "verdict": verdict,
        "color": color,
        "capital_approved": False,
    }
