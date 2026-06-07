# components/gradecard_panel.py

import streamlit as st


def render_gradecard_panel(card):
    st.markdown("---")
    st.subheader("🏛 Institutional Readiness Gradecard")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Statistical", card.get("statistical_validity", "-"))
    c2.metric("Risk", card.get("risk_management", "-"))
    c3.metric("Edge", card.get("edge_quality", "-"))
    c4.metric("Robustness", card.get("robustness", "-"))
    c5.metric("Deployability", card.get("deployability", "-"))
    c6.metric("Overall", card.get("overall", "-"))
