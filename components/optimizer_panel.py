import streamlit as st

def render_optimizer_panel(data):

    st.subheader("🚀 AI Strategy Optimizer")

    st.warning(
        f"Primary Bottleneck: {data['bottleneck']}"
    )

    st.markdown("### Recommended Improvements")

    for item in data["recommendations"]:
        st.write(f"✓ {item}")

    st.success(
        f"Expected Impact: {data['impact']}"
    )
