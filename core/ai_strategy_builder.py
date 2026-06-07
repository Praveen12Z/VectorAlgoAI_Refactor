# core/ai_strategy_builder.py

from core.universal_schema import UniversalStrategy


def build_strategy_from_text(text: str) -> dict:
    """
    AI Strategy Builder V1.
    Rule-based natural language parser for now.
    Later this will be GPT-powered.
    """

    schema = UniversalStrategy()
    txt = (text or "").lower()

    # -----------------------------
    # TREND COMPONENTS
    # -----------------------------
    if "ema" in txt or "moving average" in txt or "trend" in txt:
        schema.add_component(
            category="trend",
            component="ema_trend",
            params={
                "fast": 50,
                "slow": 200
            }
        )

    if "trendline" in txt:
        schema.add_component(
            category="trend",
            component="trendline",
            params={}
        )

    # -----------------------------
    # ENTRY COMPONENTS
    # -----------------------------
    if "pullback" in txt or "retest" in txt:
        schema.add_component(
            category="entry",
            component="pullback_entry",
            params={}
        )

    if "breakout" in txt or "break" in txt:
        schema.add_component(
            category="entry",
            component="breakout",
            params={}
        )

    if "support" in txt or "resistance" in txt:
        schema.add_component(
            category="entry",
            component="support_resistance",
            params={}
        )

    # -----------------------------
    # CONFIRMATION COMPONENTS
    # -----------------------------
    if "rsi" in txt:
        schema.add_component(
            category="confirmation",
            component="rsi_filter",
            params={
                "threshold": 55
            }
        )

    if "volume" in txt:
        schema.add_component(
            category="confirmation",
            component="volume_filter",
            params={}
        )

    if "atr" in txt or "volatility" in txt:
        schema.add_component(
            category="confirmation",
            component="atr_filter",
            params={}
        )

    # -----------------------------
    # RISK COMPONENTS
    # -----------------------------
    if "atr stop" in txt or "stop loss" in txt or "sl" in txt:
        schema.add_component(
            category="risk",
            component="atr_stop",
            params={
                "multiple": 2.0
            }
        )

    if "target" in txt or "take profit" in txt or "rr" in txt or "risk reward" in txt:
        schema.add_component(
            category="risk",
            component="rr_target",
            params={
                "rr": 3.0
            }
        )

    # -----------------------------
    # SESSION COMPONENTS
    # -----------------------------
    if "london" in txt or "new york" in txt or "ny session" in txt:
        schema.add_component(
            category="session",
            component="session_filter",
            params={}
        )

    # -----------------------------
    # NEWS / MACRO COMPONENTS
    # -----------------------------
    if "fomc" in txt or "nfp" in txt or "cpi" in txt or "news" in txt:
        schema.add_component(
            category="news",
            component="news_filter",
            params={
                "avoid_high_impact": True
            }
        )

    # -----------------------------
    # SMC / ICT COMPONENTS
    # -----------------------------
    if "liquidity" in txt or "sweep" in txt:
        schema.add_component(
            category="smc",
            component="liquidity_sweep",
            params={}
        )

    if "order block" in txt or "orderblock" in txt:
        schema.add_component(
            category="smc",
            component="order_block",
            params={}
        )

    if "fvg" in txt or "fair value gap" in txt:
        schema.add_component(
            category="smc",
            component="fair_value_gap",
            params={}
        )

    return schema.to_dict()
