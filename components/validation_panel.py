"""Streamlit presentation for chronological validation evidence."""

from __future__ import annotations

import streamlit as st


def _metric(metrics: dict, key: str, suffix: str = "") -> str:
    value = metrics.get(key)
    if value is None:
        return "—"
    if key == "num_trades":
        return str(int(value))
    return f"{float(value):.2f}{suffix}"


def render_validation_panel(validation: dict) -> None:
    st.markdown('<div class="va-section-title">Chronological validation</div>', unsafe_allow_html=True)
    st.caption(
        "Rules and cost assumptions are identical in both segments. The later segment is never used to alter this run."
    )

    status = validation.get("status", "NOT RUN")
    reason = validation.get("reason", "No validation result is available.")
    message = f"{status} — {reason}"
    if validation.get("passed"):
        st.success(message)
    elif "FAILED" in status or "DEGRADATION" in status:
        st.error(message)
    else:
        st.warning(message)

    development = validation.get("development", {})
    holdout = validation.get("holdout", {})
    development_metrics = development.get("metrics", {})
    holdout_metrics = holdout.get("metrics", {})
    left, right = st.columns(2)
    for column, label, segment, metrics in (
        (left, "Development segment", development, development_metrics),
        (right, "Hold-out segment", holdout, holdout_metrics),
    ):
        with column:
            start, end, bars = segment.get("period", (None, None, 0))
            st.markdown(f"**{label}**")
            st.caption(f"{start} → {end} · {bars:,} bars")
            c1, c2, c3 = st.columns(3)
            c1.metric("PF", _metric(metrics, "profit_factor"))
            c2.metric("Return", _metric(metrics, "total_return_pct", "%"))
            c3.metric("Trades", _metric(metrics, "num_trades"))
            st.caption(
                f"Win rate {_metric(metrics, 'win_rate_pct', '%')} · "
                f"Max drawdown {_metric(metrics, 'max_drawdown_pct', '%')}"
            )

    costs = validation.get("cost_model", {})
    full_metrics = validation.get("full", {}).get("metrics", {})
    st.info(
        "Cost assumptions per round trip: "
        f"spread {float(costs.get('spread_points', 0)):.2f} points · "
        f"slippage {float(costs.get('slippage_points_per_side', 0)):.2f} points per side · "
        f"commission {float(costs.get('commission_per_unit_round_turn', 0)):.2f} per unit. "
        f"Estimated full-sample trading cost: "
        f"{float(full_metrics.get('total_trading_cost', 0)):.2f} in account currency."
    )
    st.caption(
        "A mechanical split is only truly untouched if the trader has not viewed or tuned rules against its later period."
    )
