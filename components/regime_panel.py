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
    if development and holdout:
        context = pd.DataFrame({
            "Development": [development["high_volatility_share_pct"], development["strong_trend_share_pct"]],
            "Holdout": [holdout["high_volatility_share_pct"], holdout["strong_trend_share_pct"]],
        }, index=["High volatility", "Strong trend"])
        st.markdown("**Share of bars by market condition (%)**")
        st.bar_chart(context, horizontal=True, stack=False)
        columns = st.columns(2)
        for column, condition in zip(columns, context.index):
            value = context.loc[condition, "Holdout"]
            change = value - context.loc[condition, "Development"]
            column.metric(f"{condition} in holdout", f"{value:.1f}%", f"{change:+.1f} pp",
                          delta_color="off")

    rows = analysis.get("trade_regimes", [])
    if rows:
        st.markdown("**Trade outcomes by observed regime**")
        results = pd.DataFrame(rows)
        st.dataframe(results.rename(columns={
            "segment": "Sample", "regime": "Regime", "trades": "Trades",
            "win_rate_pct": "Win rate (%)", "profit_factor": "Profit factor",
            "average_r": "Average R", "net_pnl": "Net P&L",
        }), use_container_width=True, hide_index=True)
        if (results["trades"] < 10).any():
            st.caption("Some rows contain fewer than 10 trades. Read their returns alongside the sample count.")
    else:
        st.info("No trades could be matched to a classified regime.")
    if analysis.get("methodology"):
        with st.expander("How regimes are classified"):
            st.write(analysis["methodology"])
            st.caption("Development medians set the thresholds for both samples. Trade classification uses the completed bar before entry.")
            st.json(analysis.get("thresholds", {}))
    for observation in analysis.get("observations", []):
        st.write(f"• {observation}")
    st.caption(
        "Regime labels describe association only. They do not prove why performance changed or predict the next regime."
    )
