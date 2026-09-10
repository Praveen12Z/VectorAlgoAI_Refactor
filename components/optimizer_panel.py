import streamlit as st

def render_optimizer_panel(data):

    st.subheader("🧪 Research Experiments")

    st.warning(
        f"Primary Bottleneck: {data['bottleneck']}"
    )

    st.markdown("### Suggested experiments")

    for item in data["recommendations"]:
        st.write(f"• {item}")

    st.caption(
        f"Hypothesis to test: {data['impact']}. This is not a predicted outcome."
    )
