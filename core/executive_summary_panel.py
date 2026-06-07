import streamlit as st


def render_executive_summary(
    research,
    verdict,
    doctor,
    gradecard,
    optimizer,
    market_fit,
):

    best_market = "Unknown"

    if market_fit and len(market_fit) > 0:
        best_market = market_fit[0]["market"]

    st.subheader("📋 AI Executive Summary")

    st.info(
        f"""
Strategy Grade: {gradecard['overall']}

Best Market: {best_market}

Capital Verdict: {verdict['verdict']}

Primary Issue: {optimizer['bottleneck']}

Research Score: {research['score']}/100

Top Recommendation:
{optimizer['recommendations'][0]}
"""
    )
