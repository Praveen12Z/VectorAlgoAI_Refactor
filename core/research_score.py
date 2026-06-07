# core/research_score.py

def calculate_research_score(metrics: dict) -> dict:

    pf = float(metrics.get("profit_factor", 0))
    win_rate = float(metrics.get("win_rate_pct", 0))
    drawdown = abs(float(metrics.get("max_drawdown_pct", 0)))
    trades = int(metrics.get("num_trades", 0))
    total_return = float(metrics.get("total_return_pct", 0))

    score = 0

    # =====================================
    # Profit Factor (0-25)
    # =====================================

    if pf >= 2.0:
        score += 25
    elif pf >= 1.5:
        score += 20
    elif pf >= 1.2:
        score += 15
    elif pf >= 1.0:
        score += 10

    # =====================================
    # Win Rate (0-20)
    # =====================================

    if win_rate >= 65:
        score += 20
    elif win_rate >= 55:
        score += 15
    elif win_rate >= 45:
        score += 10
    elif win_rate >= 35:
        score += 5

    # =====================================
    # Drawdown (0-20)
    # =====================================

    if drawdown <= 5:
        score += 20
    elif drawdown <= 10:
        score += 15
    elif drawdown <= 20:
        score += 10
    elif drawdown <= 30:
        score += 5

    # =====================================
    # Return (0-15)
    # =====================================

    if total_return >= 50:
        score += 15
    elif total_return >= 25:
        score += 10
    elif total_return > 0:
        score += 5

    # =====================================
    # Sample Size (0-20)
    # =====================================

    if trades >= 100:
        score += 20
    elif trades >= 50:
        score += 15
    elif trades >= 30:
        score += 10
    elif trades >= 20:
        score += 5

    # =====================================
    # HARD VALIDITY CAPS
    # =====================================

    if trades < 10:
        score = min(score, 30)

    elif trades < 20:
        score = min(score, 50)

    elif trades < 30:
        score = min(score, 70)

    score = max(0, min(100, score))

    # =====================================
    # Grade
    # =====================================

    if score >= 85:
        grade = "A"

    elif score >= 70:
        grade = "B"

    elif score >= 55:
        grade = "C"

    elif score >= 40:
        grade = "D"

    else:
        grade = "F"

    return {
        "score": score,
        "grade": grade,
    }