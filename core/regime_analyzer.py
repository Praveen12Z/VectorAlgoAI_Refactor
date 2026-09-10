"""Descriptive regime comparison without causal or predictive claims."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


def _finite_median(series: pd.Series) -> float | None:
    values = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return float(values.median()) if not values.empty else None


def _profit_factor(pnl: pd.Series) -> float:
    values = pd.to_numeric(pnl, errors="coerce").dropna()
    gains = float(values[values > 0].sum())
    losses = abs(float(values[values < 0].sum()))
    if losses == 0:
        return math.inf if gains > 0 else 0.0
    return gains / losses


def _trade_rows(trades: pd.DataFrame, labels: pd.DataFrame, segment: str) -> list[dict[str, Any]]:
    if trades is None or trades.empty or "entry_time" not in trades.columns:
        return []
    joined = trades.copy().join(labels, on="entry_time", how="left")
    joined = joined.dropna(subset=["regime"])
    rows: list[dict[str, Any]] = []
    for regime, group in joined.groupby("regime", observed=True):
        pnl = pd.to_numeric(group.get("pnl"), errors="coerce").dropna()
        rr = pd.to_numeric(group.get("rr"), errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
        rows.append({
            "segment": segment,
            "regime": str(regime),
            "trades": int(len(group)),
            "win_rate_pct": round(float((pnl > 0).mean() * 100), 2) if not pnl.empty else 0.0,
            "profit_factor": round(_profit_factor(pnl), 2),
            "average_r": round(float(rr.mean()), 2) if not rr.empty else None,
            "net_pnl": round(float(pnl.sum()), 2) if not pnl.empty else 0.0,
        })
    return rows


def analyze_regime_shift(df: pd.DataFrame, cfg, validation: dict) -> dict:
    """Compare volatility/trend context using thresholds learned on development only."""
    development_bars = int(validation.get("development", {}).get("period", (None, None, 0))[2])
    if df is None or df.empty or development_bars <= 0 or development_bars >= len(df):
        return {"status": "UNAVAILABLE", "reason": "Validation segments are unavailable."}

    atr_columns = [item.name for item in cfg.indicators if str(item.type).lower() == "atr"]
    ema_items = sorted(
        (item for item in cfg.indicators if str(item.type).lower() == "ema"),
        key=lambda item: int(item.period),
    )
    if not atr_columns or len(ema_items) < 2:
        return {
            "status": "UNAVAILABLE",
            "reason": "ATR and at least two EMA series are required for this regime diagnostic.",
        }

    atr_column = atr_columns[0]
    fast_ema = ema_items[0].name
    slow_ema = ema_items[1].name
    required = {"close", atr_column, fast_ema, slow_ema}
    if not required.issubset(df.columns):
        return {"status": "UNAVAILABLE", "reason": "Required regime features are missing."}

    features = pd.DataFrame(index=df.index)
    features["volatility_pct"] = pd.to_numeric(df[atr_column], errors="coerce") / pd.to_numeric(
        df["close"], errors="coerce"
    ).replace(0, np.nan) * 100
    features["trend_strength"] = (
        pd.to_numeric(df[fast_ema], errors="coerce")
        - pd.to_numeric(df[slow_ema], errors="coerce")
    ).abs() / pd.to_numeric(df[atr_column], errors="coerce").replace(0, np.nan)

    development_features = features.iloc[:development_bars]
    volatility_threshold = _finite_median(development_features["volatility_pct"])
    trend_threshold = _finite_median(development_features["trend_strength"])
    if volatility_threshold is None or trend_threshold is None:
        return {"status": "UNAVAILABLE", "reason": "Regime thresholds could not be estimated."}

    volatility_label = np.where(
        features["volatility_pct"] > volatility_threshold, "High volatility", "Low volatility"
    )
    trend_label = np.where(
        features["trend_strength"] > trend_threshold, "Strong trend", "Weak trend"
    )
    features["regime"] = pd.Series(
        [f"{volatility} · {trend}" for volatility, trend in zip(volatility_label, trend_label)],
        index=features.index,
        dtype="string",
    )

    development_context = features.iloc[:development_bars]
    holdout_context = features.iloc[development_bars:]

    def context(values: pd.DataFrame) -> dict[str, float]:
        return {
            "high_volatility_share_pct": round(
                float((values["volatility_pct"] > volatility_threshold).mean() * 100), 2
            ),
            "strong_trend_share_pct": round(
                float((values["trend_strength"] > trend_threshold).mean() * 100), 2
            ),
        }

    development = validation.get("development", {})
    holdout = validation.get("holdout", {})
    rows = _trade_rows(development.get("trades"), features[["regime"]], "Development")
    rows.extend(_trade_rows(holdout.get("trades"), features[["regime"]], "Hold-out"))

    development_metrics = development.get("metrics", {})
    holdout_metrics = holdout.get("metrics", {})
    observations = [
        "Hold-out PF changed from "
        f"{float(development_metrics.get('profit_factor', 0)):.2f} to "
        f"{float(holdout_metrics.get('profit_factor', 0)):.2f}; this is observed degradation, not proof of cause."
    ]
    dev_context = context(development_context)
    hold_context = context(holdout_context)
    volatility_shift = hold_context["high_volatility_share_pct"] - dev_context["high_volatility_share_pct"]
    trend_shift = hold_context["strong_trend_share_pct"] - dev_context["strong_trend_share_pct"]
    if abs(volatility_shift) >= 10:
        observations.append(
            f"High-volatility bars changed by {volatility_shift:+.1f} percentage points in hold-out."
        )
    if abs(trend_shift) >= 10:
        observations.append(
            f"Strong-trend bars changed by {trend_shift:+.1f} percentage points in hold-out."
        )

    return {
        "status": "DESCRIPTIVE — NOT CAUSAL",
        "thresholds": {
            "development_median_atr_pct": round(volatility_threshold, 4),
            "development_median_ema_gap_atr": round(trend_threshold, 4),
        },
        "development_context": dev_context,
        "holdout_context": hold_context,
        "trade_regimes": rows,
        "observations": observations,
    }
