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

    with c1:
        st.metric("Research Score", f"{research.get('score', 0)}/100")

    with c2:
        st.metric("Capital Verdict", verdict.get("verdict", "-") )

    with c3:
        st.metric("Confidence Score", f"{risk.get('confidence_score', 0)}%")

    r1, r2 = st.columns(2)

    with r1:
        st.info(f"Risk of Ruin: {risk.get('risk_of_ruin', '-')}")

    with r2:
        st.info(f"Overfitting Risk: {risk.get('overfitting_risk', '-')}")

    num_trades = int(metrics.get("num_trades", 0))
    if num_trades < 20:
        st.warning(
            f"Statistical Validity Warning: only {num_trades} trade(s) found. "
            "Minimum recommended sample is 20–30 trades before trusting any result."
        )
