import streamlit as st


def render_executive_summary(
    research,
    verdict,
    doctor,
    gradecard,
    optimizer,
    market_fit,
):

    market_candidate = "Not assessed"

    if market_fit and len(market_fit) > 0:
        market_candidate = f"{market_fit[0]['market']} — unvalidated"

    st.subheader("📋 AI Executive Summary")

    score = research.get("score")
    score_display = f"{score}/100" if score is not None else "Unscored"

    st.info(
        f"""
Readiness Grade: {gradecard['overall']}

Cross-market candidate: {market_candidate}

Capital Verdict: {verdict['verdict']}

Primary Issue: {optimizer['bottleneck']}

Research Score: {score_display}

Next research experiment:
{optimizer['recommendations'][0]}
"""
    )
