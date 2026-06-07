# components/doctor_panel.py

import streamlit as st


def render_doctor_panel(doctor):
    st.markdown("---")
    st.subheader("🩺 Strategy Doctor")

    severity = doctor.get("severity", "LOW")

    if severity == "CRITICAL":
        st.error(f"Severity: {severity}")
    elif severity == "HIGH":
        st.warning(f"Severity: {severity}")
    else:
        st.success(f"Severity: {severity}")

    st.markdown("### Findings")
    for item in doctor.get("findings", []):
        st.write(f"• {item}")

    st.markdown("### Recommended Actions")
    for item in doctor.get("recommendations", []):
        st.write(f"• {item}")
