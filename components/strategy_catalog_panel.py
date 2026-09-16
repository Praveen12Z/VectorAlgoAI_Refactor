"""Starter specifications are separate from a user's saved evidence."""
import json
import streamlit as st
from core.strategy_catalog import CATALOG, COMMON_PROTOCOL, catalog_export, load_template


def render_strategy_catalog():
    st.subheader("Sourced strategy starters")
    st.caption("10 research templates · 1 supported baseline · 9 awaiting engine components · none validated")
    st.write("Refined means the rules are more explicit, not that returns have improved. Sources explain the underlying concepts; VectorAlgoAI's thresholds and risk rules are research adaptations.")
    selected = st.selectbox("Choose a strategy", [x['id'] for x in CATALOG],
        format_func=lambda id: next(f"{x['id']} · {x['name']}" for x in CATALOG if x['id'] == id))
    item = next(x for x in CATALOG if x['id'] == selected)
    st.markdown(f"**{item['name']} · v{item['version']}**")
    st.caption(f"{item['family']} · Proposed market: {item['market']} · {item['timeframe']}")
    st.info(item['status'])
    st.markdown(f"[Read original concept]({item['source_url']}) · Reviewed {item['reviewed_on']}")
    st.write(item['source_concept'])
    st.markdown("**Proposed rules**")
    for rule in item['rules']:
        st.write(f"• {rule}")
    st.markdown("**What we refined**")
    st.write(item['refinements'])
    st.markdown("**Where it can fail**")
    st.write(item['failure_modes'])
    if item['implementation_gaps']:
        st.warning("Automated testing blocked: " + "; ".join(item['implementation_gaps']) + ".")
    with st.expander("Shared research and execution protocol"):
        st.write(COMMON_PROTOCOL)
        st.caption("VA-001 uses the existing signal-close baseline, as disclosed in its rules. Other templates require next-open execution before testing.")
    st.download_button("Download research specification", json.dumps(catalog_export(item), indent=2),
        file_name=f"{item['id']}-v{item['version']}.json", mime="application/json")
    if not item['implementation_gaps']:
        st.caption("Opening a starter replaces the current unsaved draft and session result. Saved research remains intact; approval is required again.")
        if st.button("Open as new research draft", key=f"load_{item['id']}"):
            load_template(st.session_state, item)
            st.rerun()

