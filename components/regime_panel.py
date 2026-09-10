"""Presentation for descriptive development-versus-holdout regime evidence."""

import pandas as pd
import streamlit as st


def render_regime_panel(analysis: dict) -> None:
    st.markdown("---")
    st.subheader("🌦 Market Regime Comparison")
    if analysis.get("status") == "UNAVAILABLE":
        st.info(analysis.get("reason", "Regime evidence is unavailable."))
        return

    st.info(analysis.get("status", "DESCRIPTIVE — NOT CAUSAL"))
    development = analysis.get("development_context", {})
    holdout = analysis.get("holdout_context", {})
    left, right = st.columns(2)
    with left:
        st.markdown("**Development market context**")
        st.write(
            f"High-volatility bars: {development.get('high_volatility_share_pct', 0):.1f}%  "
            f"\nStrong-trend bars: {development.get('strong_trend_share_pct', 0):.1f}%"
        )
    with right:
        st.markdown("**Hold-out market context**")
        st.write(
            f"High-volatility bars: {holdout.get('high_volatility_share_pct', 0):.1f}%  "
            f"\nStrong-trend bars: {holdout.get('strong_trend_share_pct', 0):.1f}%"
        )

    rows = analysis.get("trade_regimes", [])
    if rows:
        st.markdown("**Trade outcomes by observed regime**")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    for observation in analysis.get("observations", []):
        st.write(f"• {observation}")
    st.caption(
        "Regime labels describe association only. They do not prove why performance changed or predict the next regime."
    )
