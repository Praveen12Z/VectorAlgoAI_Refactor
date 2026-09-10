"""Build immutable, JSON-safe evidence records for durable storage."""

from __future__ import annotations

from hashlib import sha256
import json
import math
from typing import Any

import pandas as pd

from core.evidence_policy import RESEARCH_ENGINE_VERSION


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [_json_safe(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except (ValueError, TypeError):
            pass
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def build_research_record(
    *,
    strategy_name: str,
    strategy_yaml: str,
    contract: dict,
    cfg,
    validation: dict,
) -> dict[str, Any]:
    strategy_contract = contract.get("strategy_contract", {}) or {}
    full = validation.get("full", {})
    development = validation.get("development", {})
    holdout = validation.get("holdout", {})
    full_period = full.get("period", (None, None, 0))

    record = {
        "strategy_name": (strategy_name or cfg.name or "Untitled strategy").strip(),
        "market": cfg.market,
        "timeframe": cfg.timeframe,
        "contract_version": str(strategy_contract.get("version", "unknown")),
        "contract_fingerprint": strategy_contract.get("machine_fingerprint"),
        "rules_fingerprint": strategy_contract.get("rules_fingerprint"),
        "strategy_yaml": strategy_yaml,
        "source_text": (strategy_contract.get("source", {}) or {}).get("original_text", ""),
        "evidence_engine_version": RESEARCH_ENGINE_VERSION,
        "execution_assumptions": {
            "cost_model": validation.get("cost_model", {}),
            "holdout_pct": validation.get("holdout_pct"),
            "execution_model": full.get("metrics", {}).get("execution_model"),
        },
        "data_start": str(full_period[0]) if full_period[0] is not None else None,
        "data_end": str(full_period[1]) if full_period[1] is not None else None,
        "data_bars": int(full_period[2] or 0),
        "full_metrics": full.get("metrics", {}),
        "development_metrics": development.get("metrics", {}),
        "holdout_metrics": holdout.get("metrics", {}),
        "validation_status": validation.get("status", "NOT RUN"),
        "validation_passed": bool(validation.get("passed")),
        "regime_analysis": validation.get("regime_analysis", {}),
        "trade_records": full.get("trades", pd.DataFrame()),
    }
    safe_record = _json_safe(record)
    fingerprint_payload = json.dumps(
        safe_record, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    safe_record["record_hash"] = sha256(fingerprint_payload).hexdigest()
    return safe_record
