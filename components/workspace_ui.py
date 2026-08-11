"""Shared presentation helpers for the VectorAlgoAI research workspace."""
import streamlit as st


def inject_workspace_styles() -> None:
    st.markdown(
        """
        <style>
        :root { --ink:#edf2f7; --muted:#94a3b8; --panel:#111b2d; --line:#263653;
                --blue:#66a9ff; --teal:#41d5bc; --amber:#f5bf54; --rose:#fb7185; }
        .stApp { background: #08111f; color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(8,17,31,.88); }
        [data-testid="stSidebar"] { background: #0c1728; border-right: 1px solid var(--line); }
        .block-container { max-width: 1420px; padding-top: 2.1rem; padding-bottom: 4rem; }
        h1, h2, h3 { letter-spacing: -.025em; }
        .va-eyebrow { color: var(--blue); font-size:.76rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; }
        .va-title { font-size:2rem; font-weight:700; letter-spacing:-.045em; margin:.1rem 0 .35rem; }
        .va-subtitle { color:var(--muted); font-size:1rem; margin:0 0 1.25rem; }
        .va-card { background:linear-gradient(145deg, rgba(20,33,55,.96), rgba(12,23,40,.96));
          border:1px solid var(--line); border-radius:14px; padding:1.1rem 1.2rem; min-height:108px; }
        .va-card-title { color:var(--muted); text-transform:uppercase; letter-spacing:.085em; font-size:.7rem; font-weight:700; margin-bottom:.45rem; }
        .va-card-value { font-size:1.05rem; font-weight:650; color:var(--ink); line-height:1.38; }
        .va-step { border-bottom: 2px solid #263653; color:#71809a; padding:.45rem 0 .65rem; font-size:.8rem; font-weight:650; }
        .va-step.active { border-color:var(--blue); color:#e8f1ff; }
        .va-step.done { border-color:var(--teal); color:#b9f5e9; }
        .va-status { display:inline-block; padding:.22rem .55rem; border-radius:999px; font-size:.72rem; font-weight:700; }
        .va-status.blue { color:#bcd8ff; background:#17345f; } .va-status.teal { color:#baf5e8; background:#123b39; }
        .va-status.amber { color:#ffe3a8; background:#493917; }
        div[data-testid="stMetric"] { background:rgba(17,27,45,.88); border:1px solid var(--line); padding:.85rem; border-radius:12px; }
        .stButton > button { border-radius:9px; font-weight:650; min-height:2.55rem; }
        .stButton > button[kind="primary"] { background:#2674d9; border-color:#3c8bf0; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_workspace_header() -> None:
    st.markdown('<div class="va-eyebrow">VectorAlgoAI / Research workspace</div>', unsafe_allow_html=True)
    st.markdown('<div class="va-title">Strategy Research</div>', unsafe_allow_html=True)
    st.markdown('<div class="va-subtitle">Turn a trading thesis into explicit rules, evidence and a disciplined capital-readiness decision.</div>', unsafe_allow_html=True)
    labels = [("01", "Thesis"), ("02", "Blueprint"), ("03", "Evidence"), ("04", "Diagnosis"), ("05", "Capital readiness")]
    cols = st.columns(5)
    approved = st.session_state.get("blueprint_approved", False)
    for i, (number, label) in enumerate(labels):
        state = "active" if i == 1 else ("done" if i == 0 and approved else "")
        with cols[i]:
            st.markdown(f'<div class="va-step {state}">{number} &nbsp;{label}</div>', unsafe_allow_html=True)
