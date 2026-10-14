import yaml


def compile_schema_to_yaml(schema: dict, market="XAUUSD", timeframe="1h") -> str:

    components = schema.get("components", [])
    supported = {"ema_trend", "rsi_filter", "atr_stop", "rr_target"}
    unsupported = sorted({item.get("component") for item in components} - supported)
    if unsupported:
        raise ValueError("Unsupported strategy components: " + ", ".join(unsupported))
    if not {"ema_trend", "rsi_filter"}.issubset({item.get("component") for item in components}):
        raise ValueError("MVP requires EMA trend and RSI confirmation.")
    ema_params = next(item["params"] for item in components if item["component"] == "ema_trend")
    rsi_params = next(item["params"] for item in components if item["component"] == "rsi_filter")
    fast = int(ema_params.get("fast", 20))
    slow = int(ema_params.get("slow", 50))
    threshold = float(rsi_params.get("threshold", 50))
    if not 1 <= fast < slow or not 0 <= threshold <= 100:
        raise ValueError("Invalid EMA periods or RSI threshold.")

    indicators = []
    entry_long = []
    exit_long = []

    has_ema = any(c.get("component") == "ema_trend" for c in components)
    has_rsi = any(c.get("component") == "rsi_filter" for c in components)
    has_atr = any(c.get("component") in ["atr_stop", "rr_target", "atr_filter"] for c in components)
    has_pullback = any(c.get("component") == "pullback_entry" for c in components)
    has_support_resistance = any(c.get("component") == "support_resistance" for c in components)

    if has_ema:
        indicators.extend([
            {"name": "ema20", "type": "ema", "period": fast, "source": "close"},
            {"name": "ema50", "type": "ema", "period": slow, "source": "close"},
        ])

        entry_long.extend([
            {"left": "ema20", "op": ">", "right": "ema50"},
        ])

    if has_pullback:
        entry_long.append(
            {"left": "close", "op": "<", "right": "ema20"}
        )

    if has_support_resistance:
        entry_long.append(
            {"left": "close", "op": "<=", "right": "support_zone"}
        )

    if has_rsi:
        indicators.append(
            {"name": "rsi14", "type": "rsi", "period": 14, "source": "close"}
        )

        entry_long.append(
            {"left": "rsi14", "op": ">", "right": threshold}
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
            {"name": "atr14", "type": "atr", "period": 14}
        )

    if not exit_long:
        if not any(ind.get("name") == "atr14" for ind in indicators):
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
            "long": entry_long,
            "short": []
        },
        "exit": {
            "long": exit_long,
            "short": []
        },
        "risk": {
            "capital": 10000,
            "risk_per_trade_pct": 1.0
        }
    }

    return yaml.dump(strategy, sort_keys=False)
