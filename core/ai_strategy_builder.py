# core/ai_strategy_builder.py

from core.universal_schema import UniversalStrategy


def build_strategy_from_text(text: str) -> dict:

    schema = UniversalStrategy()

    txt = text.lower()
    import re
    if re.search(r"\b(cross|crosses|crossover|short|sell|below)\b", txt):
        raise ValueError("Unsupported crossover, short, or below rule.")
    ema_match = re.search(r"ema\s*(\d+)\s*(?:is\s*)?(?:above|>)\s*ema\s*(\d+)", txt)
    rsi_match = re.search(r"rsi(?:\s*14)?\s*(?:is\s*)?(?:above|>)\s*(\d+(?:\.\d+)?)", txt)
    if not ema_match or not rsi_match:
        raise ValueError("Use EMA 20 above EMA 50 and RSI above 50.")

    # MVP is deliberately strict: any extra words must be understood.
    remainder = txt
    for match in sorted((ema_match, rsi_match), key=lambda m: m.start(), reverse=True):
        remainder = remainder[:match.start()] + " " + remainder[match.end():]
    remainder = re.sub(r"\b(?:buy|long|when|if|and|the|is|on|nasdaq|mnq|with|a|strategy|only)\b", " ", remainder)
    remainder = re.sub(r"[.,:;!?]", " ", remainder)
    if remainder.strip():
        raise ValueError("Unrecognized strategy instructions: " + remainder.strip())

    # ----------------------------------
    # TREND
    # ----------------------------------

    if (
        "ema" in txt
        or "trend" in txt
        or "moving average" in txt
    ):
        schema.add_component(
            "trend",
            "ema_trend",
            {
                "fast": int(ema_match.group(1)),
                "slow": int(ema_match.group(2))
            }
        )

    if "trendline" in txt:
        schema.add_component(
            "trend",
            "trendline",
            {}
        )

    # ----------------------------------
    # ENTRY
    # ----------------------------------

    if (
        "pullback" in txt
        or "pulls back" in txt
        or "retracement" in txt
        or "retest" in txt
    ):
        schema.add_component(
            "entry",
            "pullback_entry",
            {}
        )

    if "breakout" in txt:
        schema.add_component(
            "entry",
            "breakout",
            {}
        )

    if (
        "support" in txt
        or "resistance" in txt
    ):
        schema.add_component(
            "entry",
            "support_resistance",
            {}
        )

    # ----------------------------------
    # CONFIRMATION
    # ----------------------------------

    if "rsi" in txt:
        schema.add_component(
            "confirmation",
            "rsi_filter",
            {
                "threshold": float(rsi_match.group(1))
            }
        )

    if "volume" in txt:
        schema.add_component(
            "confirmation",
            "volume_filter",
            {}
        )

    if (
        "atr" in txt
        or "volatility" in txt
    ):
        schema.add_component(
            "confirmation",
            "atr_filter",
            {}
        )

    # ----------------------------------
    # PRICE ACTION
    # ----------------------------------

    if "bullish engulfing" in txt:
        schema.add_component(
            "price_action",
            "bullish_engulfing",
            {}
        )

    if "bearish engulfing" in txt:
        schema.add_component(
            "price_action",
            "bearish_engulfing",
            {}
        )

    if "pin bar" in txt:
        schema.add_component(
            "price_action",
            "pin_bar",
            {}
        )

    # ----------------------------------
    # SESSION
    # ----------------------------------

    if (
        "london" in txt
        or "new york" in txt
        or "ny session" in txt
    ):
        schema.add_component(
            "session",
            "session_filter",
            {}
        )

    # ----------------------------------
    # NEWS
    # ----------------------------------

    if (
        "news" in txt
        or "fomc" in txt
        or "nfp" in txt
        or "cpi" in txt
    ):
        schema.add_component(
            "news",
            "news_filter",
            {
                "avoid_high_impact": True
            }
        )

    # ----------------------------------
    # SMC / ICT
    # ----------------------------------

    if (
        "liquidity"
        in txt
        or "sweep"
        in txt
    ):
        schema.add_component(
            "smc",
            "liquidity_sweep",
            {}
        )

    if (
        "order block" in txt
        or "orderblock" in txt
    ):
        schema.add_component(
            "smc",
            "order_block",
            {}
        )

    if (
        "fair value gap" in txt
        or "fvg" in txt
    ):
        schema.add_component(
            "smc",
            "fair_value_gap",
            {}
        )

    if (
        "break of structure" in txt
        or "bos" in txt
    ):
        schema.add_component(
            "smc",
            "bos",
            {}
        )

    if (
        "change of character" in txt
        or "choch" in txt
    ):
        schema.add_component(
            "smc",
            "choch",
            {}
        )

    # ----------------------------------
    # RISK
    # ----------------------------------

    if (
        "stop loss" in txt
        or "atr stop" in txt
        or "sl" in txt
    ):
        schema.add_component(
            "risk",
            "atr_stop",
            {
                "multiple": 2
            }
        )

    if (
        "target" in txt
        or "3r" in txt
        or "2r" in txt
        or "rr" in txt
        or "risk reward" in txt
    ):
        schema.add_component(
            "risk",
            "rr_target",
            {
                "rr": 3
            }
        )

    return schema.to_dict()
