import streamlit as st


def render_executive_summary(
    research,
    verdict,
    doctor,
    gradecard,
    optimizer,
    market_fit,
):

    best_market = "Not assessed"

    if market_fit and len(market_fit) > 0:
        best_market = market_fit[0]["market"]

    st.subheader("📋 AI Executive Summary")

    score = research.get("score")
    score_display = f"{score}/100" if score is not None else "Unscored"

    st.info(
        f"""
Strategy Grade: {gradecard['overall']}

Best Market: {best_market}

Capital Verdict: {verdict['verdict']}

Primary Issue: {optimizer['bottleneck']}

Research Score: {score_display}

Next research experiment:
{optimizer['recommendations'][0]}
"""
    )
