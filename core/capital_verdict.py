# core/capital_verdict.py

def get_capital_verdict(metrics: dict) -> dict:

    pf = float(metrics.get("profit_factor", 0))
    dd = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))
    wr = float(metrics.get("win_rate_pct", 0))

    # ------------------------------
    # Verdict
    # ------------------------------

    if trades < 20:
        verdict = "⚠ INSUFFICIENT DATA"
        color = "orange"

    elif pf < 1:
        verdict = "❌ DO NOT DEPLOY"
        color = "red"

    elif dd > 25:
        verdict = "⚠ PAPER TRADE ONLY"
        color = "orange"

    elif pf > 1.3 and wr > 45:
        verdict = "✅ SMALL ALLOCATION"
        color = "green"

    elif pf > 1.6 and wr > 50 and dd < 15:
        verdict = "🚀 PROP CHALLENGE READY"
        color = "green"

    else:
        verdict = "⚠ NEEDS MORE TESTING"
        color = "orange"

    return {
        "verdict": verdict,
        "color": color,
    }