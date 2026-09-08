"""Compile the reviewed interpretation without replacing extracted parameters."""

import yaml


def _component(components: list[dict], name: str) -> dict | None:
    return next((item for item in components if item.get("component") == name), None)


def compile_schema_to_yaml(schema: dict, market="XAUUSD", timeframe="1h") -> str:
    components = schema.get("components", [])
    indicators: list[dict] = []
    entry_long: list[dict] = []
    exit_long: list[dict] = []

    ema = _component(components, "ema_trend")
    ema_periods: list[int] = []
    if ema:
        ema_periods = sorted({int(p) for p in ema.get("params", {}).get("periods", [])})
        for period in ema_periods:
            indicators.append({"name": f"ema{period}", "type": "ema", "period": period, "source": "close"})
        for fast, slow in zip(ema_periods, ema_periods[1:]):
            entry_long.append({"left": f"ema{fast}", "op": ">", "right": f"ema{slow}"})

    if _component(components, "pullback_entry") and ema_periods:
        entry_long.append({"left": "close", "op": "<", "right": f"ema{ema_periods[0]}"})
    if _component(components, "support_resistance"):
        entry_long.append({"left": "close", "op": "<=", "right": "support_zone"})

    rsi = _component(components, "rsi_filter")
    if rsi:
        params = rsi.get("params", {})
        period = int(params["period"])
        name = f"rsi{period}"
        indicators.append({"name": name, "type": "rsi", "period": period, "source": "close"})
        entry_long.append({"left": name, "op": params["op"], "right": params["threshold"]})

    atr_sources = [c for c in components if c.get("component") in {"atr_filter", "atr_stop"}]
    if atr_sources:
        period = int(atr_sources[0].get("params", {}).get("period", 14))
        indicators.append({"name": f"atr{period}", "type": "atr", "period": period})

    stop = _component(components, "atr_stop")
    target = _component(components, "rr_target")
    if stop:
        params = stop.get("params", {})
        period = int(params["period"])
        multiple = float(params["multiple"])
        atr_name = f"atr{period}"
        if not any(item["name"] == atr_name for item in indicators):
            indicators.append({"name": atr_name, "type": "atr", "period": period})
        exit_long.append({"type": "atr_sl", "atr_col": atr_name, "multiple": multiple})
        if target:
            rr = float(target.get("params", {})["rr"])
            exit_long.append({"type": "atr_tp", "atr_col": atr_name, "multiple": multiple * rr})

    risk = schema.get("risk", {})
    strategy = {
        "name": "AI Generated Universal Strategy",
        "market": market,
        "timeframe": timeframe,
        "indicators": indicators,
        "entry": {"long": entry_long, "short": []},
        "exit": {"long": exit_long, "short": []},
        "risk": {
            "capital": float(risk.get("capital", 10000)),
            "risk_per_trade_pct": float(risk.get("risk_per_trade_pct", 1.0)),
        },
        "interpretation": {
            "assumptions": schema.get("assumptions", []),
            "source_text": schema.get("source_text", ""),
        },
    }
    return yaml.dump(strategy, sort_keys=False)
