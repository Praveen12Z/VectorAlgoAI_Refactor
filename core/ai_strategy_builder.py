"""Conservative plain-English strategy interpretation.

Fallbacks are recorded as assumptions so the UI can require explicit approval.
"""

from __future__ import annotations

import re

from core.universal_schema import UniversalStrategy


def _assume(items: list[dict], field: str, value, reason: str) -> None:
    items.append({"field": field, "value": value, "reason": reason})


def _extract_research_capital(text: str) -> float | None:
    """Extract account capital whether the amount appears before or after its label."""
    amount = r"([\d][\d,]*(?:\.\d+)?)"
    patterns = (
        rf"(?:capital|account(?:\s+size)?)[^\d€$£]{{0,20}}[€$£]?\s*{amount}",
        rf"[€$£]?\s*{amount}\s*(?:[€$£]\s*)?(?:trading\s+|research\s+)?(?:account|capital)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def build_strategy_from_text(text: str) -> dict:
    schema = UniversalStrategy()
    txt = text.lower()
    assumptions: list[dict] = []

    ema_periods = sorted({int(v) for v in re.findall(r"\bema\s*[-:]?\s*(\d{1,3})\b", txt)})
    if "ema" in txt or "moving average" in txt or "trend" in txt:
        if len(ema_periods) < 2:
            ema_periods = [50, 200]
            _assume(assumptions, "EMA periods", "50 and 200", "Two EMA periods were not supplied.")
        schema.add_component("trend", "ema_trend", {"periods": ema_periods})

    if "trendline" in txt:
        schema.add_component("trend", "trendline")
    if any(term in txt for term in ("pullback", "pulls back", "retracement", "retest")):
        schema.add_component("entry", "pullback_entry")
    if "breakout" in txt:
        schema.add_component("entry", "breakout")
    if "support" in txt or "resistance" in txt:
        schema.add_component("entry", "support_resistance")

    if "rsi" in txt:
        period_match = re.search(r"\brsi\s*[-:]?\s*(\d{1,2})\b", txt)
        period = int(period_match.group(1)) if period_match else 14
        if not period_match:
            _assume(assumptions, "RSI period", 14, "No RSI lookback was supplied.")
        threshold_match = re.search(
            r"\brsi(?:\s*[-:]?\s*\d{1,2})?\s*(?:is\s*)?"
            r"(above|over|greater than|below|under|less than|>|<)\s*(\d{1,3}(?:\.\d+)?)",
            txt,
        )
        threshold = float(threshold_match.group(2)) if threshold_match else 55.0
        below_words = {"below", "under", "less than", "<"}
        op = "<" if threshold_match and threshold_match.group(1) in below_words else ">"
        if not threshold_match:
            _assume(assumptions, "RSI threshold", 55, "No RSI comparison was supplied.")
        schema.add_component("confirmation", "rsi_filter", {
            "period": period, "threshold": threshold, "op": op
        })

    if "volume" in txt:
        schema.add_component("confirmation", "volume_filter")
    if "atr" in txt or "volatility" in txt:
        atr_match = re.search(r"\batr\s*[-:]?\s*(\d{1,2})\b", txt)
        atr_period = int(atr_match.group(1)) if atr_match else 14
        if not atr_match:
            _assume(assumptions, "ATR period", 14, "No ATR lookback was supplied.")
        schema.add_component("confirmation", "atr_filter", {"period": atr_period})
    else:
        atr_period = 14

    for phrase, component in (
        ("bullish engulfing", "bullish_engulfing"),
        ("bearish engulfing", "bearish_engulfing"),
        ("pin bar", "pin_bar"),
    ):
        if phrase in txt:
            schema.add_component("price_action", component)

    sessions = [name for name in ("london", "new york", "ny") if re.search(rf"\b{name}\b", txt)]
    if sessions:
        schema.add_component("session", "session_filter", {"sessions": sessions})
    if any(term in txt for term in ("news", "fomc", "nfp", "cpi")):
        schema.add_component("news", "news_filter", {"avoid_high_impact": True})

    for terms, component in (
        (("liquidity", "sweep"), "liquidity_sweep"),
        (("order block", "orderblock"), "order_block"),
        (("fair value gap", "fvg"), "fair_value_gap"),
        (("break of structure", "bos"), "bos"),
        (("change of character", "choch"), "choch"),
    ):
        if any(term in txt for term in terms):
            schema.add_component("smc", component)

    stop_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:x\s*)?atr\s*(?:stop|sl)", txt)
    if not stop_match:
        stop_match = re.search(r"(?:stop|sl)[^\d]{0,12}(\d+(?:\.\d+)?)\s*(?:x\s*)?atr", txt)
    stop_mentioned = "stop loss" in txt or "atr stop" in txt or bool(re.search(r"\bsl\b", txt))
    if stop_match:
        schema.add_component("risk", "atr_stop", {
            "multiple": float(stop_match.group(1)), "period": atr_period
        })
    elif stop_mentioned or "atr" in txt:
        schema.add_component("risk", "atr_stop", {"multiple": 2.0, "period": atr_period})
        _assume(assumptions, "Stop distance", "2 ATR", "No executable stop distance was supplied.")

    rr_match = re.search(r"\b(\d+(?:\.\d+)?)\s*r\b", txt)
    if not rr_match:
        rr_match = re.search(r"(?:rr|risk\s*reward)[^\d]{0,8}(?:1\s*[:/]\s*)?(\d+(?:\.\d+)?)", txt)
    target_mentioned = any(term in txt for term in ("target", "rr", "risk reward"))
    if rr_match:
        schema.add_component("risk", "rr_target", {"rr": float(rr_match.group(1))})
    elif target_mentioned:
        schema.add_component("risk", "rr_target", {"rr": 2.0})
        _assume(assumptions, "Profit target", "2R", "No executable reward/risk target was supplied.")

    risk_match = re.search(r"(?:risk(?:ing)?|risk per trade)[^\d%]{0,12}(\d+(?:\.\d+)?)\s*%", txt)
    risk_pct = float(risk_match.group(1)) if risk_match else 1.0
    if not risk_match:
        _assume(assumptions, "Risk per trade", "1%", "No position-risk percentage was supplied.")

    explicit_capital = _extract_research_capital(txt)
    capital = explicit_capital if explicit_capital is not None else 10000.0
    if explicit_capital is None:
        _assume(assumptions, "Research capital", 10000, "No account capital was supplied.")

    result = schema.to_dict()
    result["risk"] = {"capital": capital, "risk_per_trade_pct": risk_pct}
    result["assumptions"] = assumptions
    result["source_text"] = text.strip()
    return result
