# core/strategy_optimizer.py

def optimize_strategy(metrics: dict):

    pf = float(metrics.get("profit_factor", 0))
    wr = float(metrics.get("win_rate_pct", 0))
    dd = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))

    bottleneck = "Unknown"
    impact = "Unknown"

    recommendations = []

    if trades < 30:

        bottleneck = "Insufficient Sample Size"

        recommendations.extend([
            "Increase test period",
            "Increase signal frequency",
            "Gather at least 30 trades"
        ])

        impact = "Higher confidence"

    elif pf < 1.10:

        bottleneck = "No Demonstrated Edge"

        recommendations.extend([
            "Test entry selectivity as one controlled change",
            "Test stop and target placement separately",
            "Add realistic costs before comparing variants",
            "Keep an untouched hold-out sample"
        ])

        impact = "A measurable improvement over the baseline"

    elif dd > 20:

        bottleneck = "High Drawdown"

        recommendations.extend([
            "Reduce risk per trade",
            "Use tighter stop losses",
            "Avoid high-volatility periods"
        ])

        impact = "Lower drawdown"

    elif wr < 45:

        bottleneck = "Weak Win Rate"

        recommendations.extend([
            "Add confirmation filters",
            "Improve setup quality",
            "Avoid weak pullbacks"
        ])

        impact = "Higher win rate"

    else:

        bottleneck = "No Major Weakness"

        recommendations.extend([
            "Forward test strategy",
            "Perform out-of-sample validation"
        ])

        impact = "Further validation"

    return {
        "bottleneck": bottleneck,
        "recommendations": recommendations,
        "impact": impact,
    }
