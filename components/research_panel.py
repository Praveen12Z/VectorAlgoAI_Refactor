# components/research_panel.py

import streamlit as st


def render_research_panel(cfg, data_start, data_end, data_bars, research, verdict, risk, metrics):
    st.success(
        f"Parsed strategy: {cfg.name} · Market: {cfg.market} · Timeframe: {cfg.timeframe}"
    )

    st.info(
        f"Data Range Loaded: {data_start} → {data_end} · Bars: {data_bars}"
    )

    st.subheader("🧠 Research Report")

    c1, c2, c3 = st.columns(3)

    score = research.get("score")
    confidence = risk.get("confidence_score")

    with c1:
        st.metric("Research Score", f"{score}/100" if score is not None else "Unscored")

    with c2:
        st.metric("Capital Verdict", verdict.get("verdict", "-") )

    with c3:
        st.metric("Evidence Maturity", f"{confidence}%" if confidence is not None else "Unscored")

    r1, r2 = st.columns(2)

    with r1:
        st.info(f"Risk of Ruin: {risk.get('risk_of_ruin', '-')}")

    with r2:
        st.info(f"Overfitting Risk: {risk.get('overfitting_risk', '-')}")

    num_trades = int(metrics.get("num_trades", 0))
    if num_trades < 30:
        st.warning(
            f"Statistical Validity Warning: only {num_trades} trade(s) found. "
            "At least 30 trades are required before VectorAlgoAI scores edge, risk or readiness."
        )
