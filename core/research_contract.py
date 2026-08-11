"""Validation for the facts a research run must satisfy before backtesting."""

from __future__ import annotations

from typing import Any


def strategy_contract_issues(raw: dict[str, Any]) -> list[str]:
    """Return user-facing blockers instead of letting an invalid test fail later.

    This deliberately validates data coverage as well as syntax. A session-range
    strategy needs candles during that session; a regular-hours index feed cannot
    supply those candles truthfully.
    """
    issues: list[str] = []
    entry = raw.get("entry", {}) or {}
    if not (entry.get("long") or entry.get("short")):
        issues.append(
            "No executable entry rule was generated. Define the breakout trigger "
            "(for example, close beyond the Asia high/low and any buffer or retest)."
        )

    contract = raw.get("research_contract", {}) or {}
    if contract.get("requires_extended_hours"):
        issues.append(
            "Asia-session high/low cannot be tested with the current NAS100 data source. "
            "This MVP maps NAS100 to Yahoo's ^NDX index feed, which has regular US "
            "index hours only. Use a 24-hour NQ futures or NAS100 CFD data feed before "
            "running this research."
        )
    return issues
