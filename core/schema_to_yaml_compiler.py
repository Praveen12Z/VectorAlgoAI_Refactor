# core/schema_to_yaml_compiler.py

import yaml


def compile_schema_to_yaml(schema: dict, market="XAUUSD", timeframe="1h") -> str:
    """
    Converts Universal Strategy Schema into current YAML strategy format.
    V1 supports:
    - ema_trend
    - rsi_filter
    - pullback_entry
    - support_resistance placeholder
    - rr_target
    - atr_stop
    - news_filter placeholder
    - liquidity_sweep placeholder
    """

    components = schema.get("components", [])

    indicators = []
    entry_long = []
    exit_long = []

    has_ema = any(c.get("component") == "ema_trend" for c in components)
    has_rsi = any(c.get("component") == "rsi_filter" for c in components)
    has_atr = any(c.get("component") in ["atr_stop", "rr_target"] for c in components)
    has_pullback = any(c.get("component") == "pullback_entry" for c in components)

    if has_ema:
        indicators.extend([
            {"name": "ema20", "type": "ema", "period": 20, "source": "close"},
            {"name": "ema50", "type": "ema", "period": 50, "source": "close"},
            {"name": "ema200", "type": "ema", "period": 200, "source": "close"},
        ])

        entry_long.extend([
            {"left": "ema50", "op": ">", "right": "ema200"},
            {"left": "ema20", "op": ">", "right": "ema50"},
        ])

    if has_pullback:
        entry_long.append(
            {"left": "close", "op": "<", "right": "ema20"}
        )

    if has_rsi:
        indicators.append(
            {"name": "rsi14", "type": "rsi", "period": 14, "source": "close"}
        )

        entry_long.append(
            {"left": "rsi14", "op": ">", "right": 55}
        )

    if has_atr:
        indicators.append(
            {"name": "atr14", "type": "atr", "period": 14}
        )

        exit_long.extend([
            {"type": "atr_sl", "atr_col": "atr14", "multiple": 2.0},
            {"type": "atr_tp", "atr_col": "atr14", "multiple": 3.0},
        ])

    if not indicators:
        indicators.append(
            {"name": "rsi14", "type": "rsi", "period": 14, "source": "close"}
        )
        entry_long.append(
            {"left": "rsi14", "op": ">", "right": 50}
        )

    if not exit_long:
        indicators.append(
            {"name": "atr14", "type": "atr", "period": 14}
        )
        exit_long.extend([
            {"type": "atr_sl", "atr_col": "atr14", "multiple": 2.0},
            {"type": "atr_tp", "atr_col": "atr14", "multiple": 3.0},
        ])

    strategy = {
        "name": "AI Generated Universal Strategy",
        "market": market,
        "timeframe": timeframe,
        "indicators": indicators,
        "entry": {
            "long": entry_long
        },
        "exit": {
            "long": exit_long
        },
        "risk": {
            "capital": 10000,
            "risk_per_trade_pct": 1.0
        }
    }

    return yaml.dump(strategy, sort_keys=False)
