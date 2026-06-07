# components/root_cause_panel.py

import streamlit as st


def render_root_cause_panel(root_cause):
    st.markdown("---")
    st.subheader("🔍 Root Cause Analysis")

    st.error(f"Primary Issue: {root_cause.get('main_problem', '-')}")
    st.write(root_cause.get("explanation", ""))

    st.markdown("### Suggested Improvements")
    for item in root_cause.get("fixes", []):
        st.write(f"• {item}")
