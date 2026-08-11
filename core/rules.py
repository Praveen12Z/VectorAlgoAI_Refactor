"""Compatibility rule interface used by the legacy signal engine.

The application has two rule entry points.  ``rule_engine`` is the canonical
implementation; this small module preserves the import used by
``signal_engine`` so both paths evaluate the same rule semantics.
"""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from .rule_engine import eval_rule_group


def evaluate_rule_group(
    df: pd.DataFrame, idx: int, group: Mapping[str, Any]
) -> bool:
    """Evaluate one ``all``/``any`` rule group at a single bar."""
    return eval_rule_group(df, idx, dict(group))
