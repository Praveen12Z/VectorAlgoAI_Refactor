"""Canonical Strategy Contract v1 and executable-capability gate.

The contract records what the trader said, how each material rule is treated,
and the exact machine payload approved for research.  It is deliberately kept
inside the existing YAML document so older execution code can continue reading
``entry``/``exit``/``risk`` while the product gains an auditable truth layer.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


CONTRACT_VERSION = "1.0"
VALID_STATUSES = {"executable", "manual", "ambiguous", "unsupported"}


CAPABILITIES: dict[str, dict[str, str]] = {
    "ema_trend": {
        "status": "executable",
        "executor": "ema_alignment",
        "reason": "EMA periods and alignment are supported by the canonical rule engine.",
    },
    "pullback_entry": {
        "status": "executable",
        "executor": "ema_pullback",
        "reason": "A close-price pullback to the fastest configured EMA is supported.",
    },
    "rsi_filter": {
        "status": "executable",
        "executor": "rsi_comparison",
        "reason": "RSI period, comparison and threshold are supported.",
    },
    "atr_filter": {
        "status": "executable",
        "executor": "atr_calculation",
        "reason": "ATR calculation is supported as an input to protective exits.",
    },
    "atr_stop": {
        "status": "executable",
        "executor": "atr_protective_stop",
        "reason": "ATR stop distance is supported by the backtest execution model.",
    },
    "rr_target": {
        "status": "executable",
        "executor": "risk_reward_target",
        "reason": "A fixed R-multiple target is supported when an executable stop exists.",
    },
    "trendline": {
        "status": "manual",
        "executor": "none",
        "reason": "No objective trendline construction and touch policy has been approved.",
    },
    "support_resistance": {
        "status": "manual",
        "executor": "none",
        "reason": "Zone construction, freshness, tolerance and invalidation still require trader definition.",
    },
    "breakout": {
        "status": "ambiguous",
        "executor": "none",
        "reason": "Breakout lookback, trigger price, close/wick policy, buffer and retest rules are missing.",
    },
    "session_filter": {
        "status": "unsupported",
        "executor": "none",
        "reason": "The current data/execution path does not enforce session windows reliably.",
    },
    "news_filter": {
        "status": "unsupported",
        "executor": "none",
        "reason": "No point-in-time economic-news dataset is connected to the backtester.",
    },
    "volume_filter": {
        "status": "ambiguous",
        "executor": "none",
        "reason": "The volume source, comparison window and threshold are not defined.",
    },
    "bullish_engulfing": {
        "status": "unsupported",
        "executor": "none",
        "reason": "The candle-pattern executor is not connected to the canonical backtester.",
    },
    "bearish_engulfing": {
        "status": "unsupported",
        "executor": "none",
        "reason": "The candle-pattern executor is not connected to the canonical backtester.",
    },
    "pin_bar": {
        "status": "ambiguous",
        "executor": "none",
        "reason": "Body, wick, location and rejection thresholds are not defined.",
    },
    "liquidity_sweep": {
        "status": "manual",
        "executor": "none",
        "reason": "The liquidity level and sweep/reclaim definition require labelled examples.",
    },
    "order_block": {
        "status": "manual",
        "executor": "none",
        "reason": "Order-block origin, mitigation, freshness and invalidation require labelled examples.",
    },
    "fair_value_gap": {
        "status": "manual",
        "executor": "none",
        "reason": "Gap construction, minimum size, fill and invalidation require labelled examples.",
    },
    "bos": {
        "status": "manual",
        "executor": "none",
        "reason": "Swing selection and break-of-structure confirmation require labelled examples.",
    },
    "choch": {
        "status": "manual",
        "executor": "none",
        "reason": "Swing selection and change-of-character confirmation require labelled examples.",
    },
}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def machine_fingerprint(strategy: dict[str, Any]) -> str:
    """Fingerprint the executable payload, excluding descriptive contract data."""
    payload = {key: value for key, value in strategy.items() if key != "strategy_contract"}
    return _digest(payload)


def rules_fingerprint(rules: list[dict[str, Any]]) -> str:
    return _digest(rules)


def _rule_statement(component: dict[str, Any]) -> str:
    name = str(component.get("component", "unknown_rule")).replace("_", " ")
    params = component.get("params", {}) or {}
    if not params:
        return name.title()
    rendered = ", ".join(f"{key.replace('_', ' ')}={value}" for key, value in sorted(params.items()))
    return f"{name.title()} ({rendered})"


def _classify(component: dict[str, Any], component_names: set[str]) -> dict[str, str]:
    name = str(component.get("component", ""))
    capability = dict(CAPABILITIES.get(name, {
        "status": "unsupported",
        "executor": "none",
        "reason": "This rule has no registered execution capability.",
    }))
    params = component.get("params", {}) or {}

    if name == "ema_trend" and len(params.get("periods", [])) < 2:
        capability.update(status="ambiguous", executor="none", reason="At least two EMA periods are required.")
    elif name == "pullback_entry" and "ema_trend" not in component_names:
        capability.update(status="ambiguous", executor="none", reason="The pullback reference level is not defined.")
    elif name == "rsi_filter" and not {"period", "threshold", "op"}.issubset(params):
        capability.update(status="ambiguous", executor="none", reason="RSI period, threshold and comparison are required.")
    elif name == "atr_stop" and not {"period", "multiple"}.issubset(params):
        capability.update(status="ambiguous", executor="none", reason="ATR period and stop multiple are required.")
    elif name == "rr_target" and "atr_stop" not in component_names:
        capability.update(status="ambiguous", executor="none", reason="A target in R requires an executable protective stop.")
    return capability


def build_strategy_contract(schema: dict[str, Any], market: str, timeframe: str) -> dict[str, Any]:
    components = list(schema.get("components", []) or [])
    component_names = {str(item.get("component", "")) for item in components}
    rules: list[dict[str, Any]] = []
    for index, component in enumerate(components, start=1):
        capability = _classify(component, component_names)
        rules.append({
            "rule_id": f"R-{index:03d}",
            "domain": str(component.get("category", "other")),
            "component": str(component.get("component", "unknown_rule")),
            "statement": _rule_statement(component),
            "parameters": deepcopy(component.get("params", {}) or {}),
            "status": capability["status"],
            "material": True,
            "executor": capability["executor"],
            "reason": capability["reason"],
        })

    risk = deepcopy(schema.get("risk", {}) or {})
    rules.append({
        "rule_id": f"R-{len(rules) + 1:03d}",
        "domain": "risk",
        "component": "risk_budget",
        "statement": (
            f"Risk {risk.get('risk_per_trade_pct', 'unspecified')}% of "
            f"{risk.get('capital', 'unspecified')} research capital per trade"
        ),
        "parameters": risk,
        "status": "executable" if float(risk.get("capital", 0)) > 0 and 0 < float(risk.get("risk_per_trade_pct", 0)) <= 100 else "ambiguous",
        "material": True,
        "executor": "equity_risk_sizing",
        "reason": "Capital and per-trade risk are explicit." if risk else "Capital and per-trade risk are required.",
    })

    counts = {status: sum(rule["status"] == status for rule in rules) for status in sorted(VALID_STATUSES)}
    contract = {
        "version": CONTRACT_VERSION,
        "identity": {
            "name": "AI Generated Universal Strategy",
            "market": market,
            "timeframe": timeframe,
            "direction": "long",
        },
        "source": {
            "original_text": schema.get("source_text", ""),
            "assumptions": deepcopy(schema.get("assumptions", []) or []),
        },
        "rules": rules,
        "coverage": {
            "total_rules": len(rules),
            **counts,
            "material_blockers": sum(
                rule["material"] and rule["status"] != "executable" for rule in rules
            ),
        },
        "approval": {
            "state": "draft",
            "assumptions_accepted": False,
            "approved_rule_ids": [],
            "approved_machine_fingerprint": None,
            "approved_rules_fingerprint": None,
        },
    }
    contract["rules_fingerprint"] = rules_fingerprint(rules)
    return contract


def attach_strategy_contract(
    strategy: dict[str, Any], schema: dict[str, Any], market: str, timeframe: str
) -> dict[str, Any]:
    result = deepcopy(strategy)
    contract = build_strategy_contract(schema, market, timeframe)
    result["strategy_contract"] = contract
    contract["machine_fingerprint"] = machine_fingerprint(result)
    return result


def contract_gate_issues(strategy: dict[str, Any], require_approval: bool = False) -> list[str]:
    contract = strategy.get("strategy_contract")
    if not isinstance(contract, dict):
        return ["Strategy Contract v1 is missing."]
    issues: list[str] = []
    if str(contract.get("version")) != CONTRACT_VERSION:
        issues.append(f"Strategy Contract version must be {CONTRACT_VERSION}.")

    rules = contract.get("rules")
    if not isinstance(rules, list) or not rules:
        return issues + ["The strategy contract contains no rules."]
    if contract.get("rules_fingerprint") != rules_fingerprint(rules):
        issues.append("The contract rules changed after generation; rebuild and review the Blueprint.")
    if contract.get("machine_fingerprint") != machine_fingerprint(strategy):
        issues.append("The executable YAML changed after contract generation; rebuild and review the Blueprint.")

    seen: set[str] = set()
    for rule in rules:
        rule_id = str(rule.get("rule_id", "missing id"))
        if rule_id in seen:
            issues.append(f"Duplicate rule id: {rule_id}.")
        seen.add(rule_id)
        status = rule.get("status")
        if status not in VALID_STATUSES:
            issues.append(f"{rule_id} has invalid capability status: {status}.")
        elif rule.get("material", True) and status != "executable":
            issues.append(
                f"{rule_id} · {str(rule.get('component', 'rule')).replace('_', ' ').title()} "
                f"is {status}: {rule.get('reason', 'No reason recorded.')}"
            )

    if not any(rule.get("domain") == "entry" and rule.get("status") == "executable" for rule in rules):
        issues.append("At least one executable entry trigger is required.")
    if not any(rule.get("component") == "atr_stop" and rule.get("status") == "executable" for rule in rules):
        issues.append("An executable protective stop is required for risk-sized testing.")

    approval = contract.get("approval", {}) or {}
    assumptions = (contract.get("source", {}) or {}).get("assumptions", []) or []
    if require_approval:
        if approval.get("state") != "approved":
            issues.append("The Strategy Contract has not been approved.")
        if assumptions and not approval.get("assumptions_accepted"):
            issues.append("Inferred assumptions have not been accepted.")
        if approval.get("approved_machine_fingerprint") != contract.get("machine_fingerprint"):
            issues.append("The approved executable fingerprint does not match the current contract.")
        if approval.get("approved_rules_fingerprint") != contract.get("rules_fingerprint"):
            issues.append("The approved rule fingerprint does not match the current contract.")
    return issues


def approve_strategy_contract(strategy: dict[str, Any], assumptions_accepted: bool) -> dict[str, Any]:
    result = deepcopy(strategy)
    issues = contract_gate_issues(result, require_approval=False)
    if issues:
        raise ValueError("Strategy Contract cannot be approved: " + " | ".join(issues))
    contract = result["strategy_contract"]
    assumptions = (contract.get("source", {}) or {}).get("assumptions", []) or []
    if assumptions and not assumptions_accepted:
        raise ValueError("Review and accept the disclosed assumptions before approval.")
    contract["approval"] = {
        "state": "approved",
        "assumptions_accepted": bool(assumptions_accepted or not assumptions),
        "approved_rule_ids": [rule["rule_id"] for rule in contract["rules"]],
        "approved_machine_fingerprint": contract["machine_fingerprint"],
        "approved_rules_fingerprint": contract["rules_fingerprint"],
    }
    return result


def require_approved_strategy_contract(strategy: dict[str, Any]) -> None:
    """Raise a user-facing error unless the exact contract is approved."""
    issues = contract_gate_issues(strategy, require_approval=True)
    if issues:
        raise ValueError("Strategy Contract blocked this backtest: " + " | ".join(issues))
