"""Shared evidence-honesty rules for research outputs."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


MIN_SCORABLE_TRADES = 30
RESEARCH_ENGINE_VERSION = "strategy-contract-1.1-evidence-1"

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
