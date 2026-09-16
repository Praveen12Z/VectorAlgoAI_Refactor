"""Experiment metadata lives in the existing JSON envelope; evidence is append-only."""
from copy import deepcopy
from hashlib import sha256
import json

DECISIONS = ("Inconclusive", "Rejected for deployment", "Awaiting validation")


def metadata(record):
    return (record.get("execution_assumptions") or {}).get("experiment") or {}


def annotate(record, *, version, hypothesis, parent_record_hash=None,
             decision="Inconclusive", notes="", review=False):
    if decision not in DECISIONS:
        raise ValueError("Unsupported research decision")
    result = deepcopy(record)
    for key in ("id", "user_id", "created_at", "record_hash"):
        result.pop(key, None)
    result.setdefault("execution_assumptions", {})["experiment"] = {
        "version": version.strip(), "hypothesis": hypothesis.strip(),
        "parent_record_hash": parent_record_hash, "decision": decision,
        "notes": notes.strip(), "kind": "review" if review else "run",
        "review_of_record_hash": record.get("record_hash") if review else None,
    }
    result["record_hash"] = sha256(json.dumps(result, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    return result


def comparison(left, right):
    rows = []
    for key in ("market", "timeframe", "data_start", "data_end", "data_bars",
                "rules_fingerprint", "evidence_engine_version", "validation_status"):
        rows.append({"Field": key, "A": left.get(key), "B": right.get(key)})
    for key in ("cost_model", "holdout_pct", "execution_model"):
        rows.append({"Field": key, "A": json.dumps((left.get("execution_assumptions") or {}).get(key), sort_keys=True),
                     "B": json.dumps((right.get("execution_assumptions") or {}).get(key), sort_keys=True)})
    for segment in ("full_metrics", "development_metrics", "holdout_metrics"):
        for metric in ("num_trades", "total_return_pct", "profit_factor", "win_rate_pct", "max_drawdown_pct"):
            rows.append({"Field": f"{segment}: {metric}",
                         "A": (left.get(segment) or {}).get(metric),
                         "B": (right.get(segment) or {}).get(metric)})
    return rows
