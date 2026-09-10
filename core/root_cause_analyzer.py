# core/root_cause_analyzer.py

def analyze_root_cause(metrics: dict) -> dict:

    pf = float(metrics.get("profit_factor", 0))
    wr = float(metrics.get("win_rate_pct", 0))
    dd = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))
    total_return = float(metrics.get("total_return_pct", 0))

    main_problem = "Unknown"
    explanation = ""
    fixes = []

    if trades < 30:

        main_problem = "Insufficient Sample Size"

        explanation = (
            f"Only {trades} trades were generated. "
            "The strategy lacks enough evidence."
        )

        fixes = [
            "Expand test period",
            "Increase signal frequency",
            "Gather at least 30 trades",
        ]

    elif pf < 1.10:

        main_problem = "No Demonstrated Edge"

        explanation = (
            f"Profit Factor is {pf:.2f}. The baseline is too close to breakeven "
            "to survive unmodelled trading costs with confidence."
        )

        fixes = [
            "Improve entry quality",
            "Test entry selectivity as one controlled change",
            "Test stop and target placement separately",
            "Add realistic costs before comparing variants",
        ]

    elif dd > 25:

        main_problem = "Excessive Drawdown"

        explanation = (
            f"Drawdown reached {dd:.2f}%."
        )

        fixes = [
            "Reduce risk per trade",
            "Use tighter exits",
            "Improve stop-loss placement",
        ]

    elif wr < 40:

        main_problem = "Low Win Rate"

        explanation = (
            f"Win rate is only {wr:.1f}%."
        )

        fixes = [
            "Improve entry timing",
            "Use confirmation filters",
            "Avoid low-quality setups",
        ]

    elif total_return <= 0:

        main_problem = "No Positive Return"

        explanation = (
            "Strategy failed to generate positive return."
        )

        fixes = [
            "Rebuild strategy logic",
            "Review entry and exit rules",
        ]

    elif not metrics.get("oos_passed"):

        main_problem = "Robustness Not Verified"

        explanation = metrics.get(
            "validation_reason",
            "The strategy has not passed an unchanged chronological hold-out test.",
        )

        fixes = [
            "Keep the strategy rules frozen",
            "Collect enough trades in both development and hold-out segments",
            "Reject the version if its edge does not persist on hold-out data",
        ]

    else:

        main_problem = "No Major Weakness Detected"

        explanation = (
            "Metrics appear acceptable."
        )

        fixes = [
            "Continue forward testing",
            "Perform out-of-sample validation",
        ]

    return {
        "main_problem": main_problem,
        "explanation": explanation,
        "fixes": fixes,
    }
