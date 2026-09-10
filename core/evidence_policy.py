"""Shared evidence-honesty rules for research outputs."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


MIN_SCORABLE_TRADES = 30
MIN_DEMONSTRATED_PROFIT_FACTOR = 1.10
RESEARCH_ENGINE_VERSION = "strategy-contract-1.1-validation-2"

_STALE_RESEARCH_KEYS = (
    "blueprint_yaml",
    "strategy_yaml",
    "approved_strategy_yaml",
    "evidence_yaml_editor",
    "blueprint_schema",
    "blueprint_approved",
    "blueprint_assumptions_accepted",
    "bt_result",
)


def trade_count(metrics: dict[str, Any] | None) -> int:
    try:
        return max(0, int((metrics or {}).get("num_trades", 0)))
    except (TypeError, ValueError):
        return 0


def evidence_is_sufficient(metrics: dict[str, Any] | None) -> bool:
    return trade_count(metrics) >= MIN_SCORABLE_TRADES


def baseline_edge_is_demonstrated(metrics: dict[str, Any] | None) -> bool:
    """Require more than accounting breakeven before describing an edge."""
    if not evidence_is_sufficient(metrics):
        return False
    try:
        profit_factor = float((metrics or {}).get("profit_factor", 0))
        total_return = float((metrics or {}).get("total_return_pct", 0))
    except (TypeError, ValueError):
        return False
    return profit_factor >= MIN_DEMONSTRATED_PROFIT_FACTOR and total_return > 0


def robustness_is_verified(metrics: dict[str, Any] | None) -> bool:
    """Robustness requires both friction-aware and out-of-sample evidence."""
    values = metrics or {}
    return bool(values.get("costs_included") and values.get("oos_passed"))


def invalidate_stale_research_state(state: MutableMapping[str, Any]) -> bool:
    """Clear incompatible generated research after the engine contract changes."""
    if state.get("research_engine_version") == RESEARCH_ENGINE_VERSION:
        return False

    had_research = any(state.get(key) for key in _STALE_RESEARCH_KEYS)
    for key in _STALE_RESEARCH_KEYS:
        state.pop(key, None)

    state["research_engine_version"] = RESEARCH_ENGINE_VERSION
    if had_research:
        state["active_workspace_stage"] = "thesis"
        state["active_workspace_view"] = "thesis"
        state["research_reset_notice"] = (
            "The research engine changed, so the previous Blueprint and evidence were invalidated. "
            "Your strategy text was preserved; rebuild the contract before testing."
        )
    return had_research
