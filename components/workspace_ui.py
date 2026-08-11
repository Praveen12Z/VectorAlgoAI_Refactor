"""Presentation helpers for the VectorAlgoAI research workspace."""
import streamlit as st


STAGES = (
    ("thesis", "01", "Thesis"),
    ("blueprint", "02", "Blueprint"),
    ("evidence", "03", "Evidence"),
    ("diagnosis", "04", "Diagnosis"),
    ("readiness", "05", "Readiness"),
)


def inject_workspace_styles() -> None:
    """Keep the application visually calm: one accent colour, not a trading terminal."""
    st.markdown("""
    <style>
      :root { --bg:#090d14; --surface:#101722; --surface-2:#141d2a; --line:#263243;
              --text:#edf2f7; --muted:#8b98aa; --blue:#7fb0ff; --blue-bg:#142845; }
      .stApp { background:var(--bg); color:var(--text); }
      [data-testid="stHeader"] { background:rgba(9,13,20,.94); border-bottom:1px solid rgba(38,50,67,.75); }
      [data-testid="stSidebar"] { background:#0c111a; border-right:1px solid var(--line); }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding:1.1rem .8rem; }
      .block-container { max-width:1240px; padding:2.1rem 2.25rem 4rem; }
      h1,h2,h3 { color:var(--text); letter-spacing:-.035em; }
      .va-brand { font-size:.95rem; font-weight:760; letter-spacing:-.025em; color:#f6f8fb; }
      .va-brand b { color:var(--blue); font-weight:760; }
      .va-brand-sub { color:var(--muted); font-size:.72rem; margin-top:.18rem; }
      .va-side-label { color:#68778a; font-size:.67rem; font-weight:750; letter-spacing:.11em; text-transform:uppercase; margin:1.5rem 0 .48rem; }
      .va-research-card { background:var(--surface); border:1px solid var(--line); border-radius:8px; padding:.75rem; }
      .va-research-name { color:var(--text); font-size:.82rem; font-weight:650; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .va-research-meta { color:var(--muted); font-size:.72rem; margin-top:.22rem; }
      .va-eyebrow { color:var(--blue); font-size:.68rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; }
      .va-title { font-size:2rem; font-weight:720; line-height:1.1; letter-spacing:-.05em; margin:.35rem 0 .45rem; }
      .va-subtitle { color:var(--muted); font-size:.94rem; max-width:700px; line-height:1.55; margin:0 0 1.7rem; }
      .va-rule { border:0; border-top:1px solid var(--line); margin:1.3rem 0 1.6rem; }
      .va-card { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:1rem; min-height:104px; }
      .va-card-title { color:var(--muted); font-size:.68rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; margin-bottom:.48rem; }
      .va-card-value { color:var(--text); font-size:.92rem; line-height:1.45; font-weight:590; }
      .va-section-title { color:var(--text); font-size:1.12rem; font-weight:700; margin:2.2rem 0 .22rem; letter-spacing:-.02em; }
      .va-section-copy { color:var(--muted); font-size:.88rem; line-height:1.5; margin-bottom:1rem; }
      .va-evidence-banner { background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--blue); border-radius:8px; padding:1rem 1.1rem; margin:.8rem 0 1.35rem; }
      .va-evidence-kicker { color:var(--blue); font-size:.68rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; }
      .va-evidence-title { color:var(--text); font-size:1rem; font-weight:690; margin:.24rem 0; }
      .va-evidence-meta { color:var(--muted); font-size:.82rem; }
      .va-status { display:inline-block; background:var(--blue-bg); border:1px solid #2c4b70; color:#c9ddff; padding:.24rem .54rem; border-radius:999px; font-size:.7rem; font-weight:700; }
      div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:9px; padding:.85rem .9rem; }
      div[data-testid="stMetricLabel"] { color:var(--muted); font-size:.72rem; }
      div[data-testid="stMetricValue"] { color:var(--text); font-size:1.28rem; }
      .stButton > button { min-height:2.4rem; border-radius:7px; font-weight:650; border-color:#344357; background:transparent; color:#c7d1df; }
      .stButton > button:hover { border-color:#6684ab; color:#f4f7fb; background:#121c29; }
      .stButton > button[kind="primary"] { background:#2d67b5; border-color:#417bd0; color:white; }
      .stButton > button[kind="primary"]:hover { background:#3976c8; }
      [class*="st-key-header_stage_"] button { min-height:3.05rem; text-align:left; padding:.55rem .35rem; border:0; border-bottom:2px solid var(--line); border-radius:0; font-size:.76rem; background:transparent; color:var(--muted); box-shadow:none; }
      [class*="st-key-header_stage_"] button[kind="primary"] { border-color:var(--blue); color:var(--text); }
      [class*="st-key-sidebar_stage_"] button { border:0; text-align:left; min-height:2.15rem; padding:.3rem .55rem; font-size:.82rem; }
      [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background:#0d141e !important; border-color:#334154 !important; color:var(--text) !important; border-radius:7px !important; }
      .stTabs [data-baseweb="tab-list"] { gap:1.2rem; border-bottom:1px solid var(--line); }
      .stTabs [data-baseweb="tab"] { color:var(--muted); padding:.55rem .1rem; }
      .stTabs [aria-selected="true"] { color:var(--text); border-bottom-color:var(--blue) !important; }
      .stDataFrame { border:1px solid var(--line); border-radius:8px; overflow:hidden; }
    </style>
    """, unsafe_allow_html=True)


def render_workspace_header(active_stage: str = "thesis") -> None:
    st.markdown('<div class="va-eyebrow">VectorAlgoAI · strategy research</div>', unsafe_allow_html=True)
    st.markdown('<div class="va-title">Build evidence before you risk capital.</div>', unsafe_allow_html=True)
    st.markdown('<div class="va-subtitle">Make the trading logic explicit, test it honestly, then decide the next research action.</div>', unsafe_allow_html=True)
    columns = st.columns(5, gap="small")
    for column, (stage, number, label) in zip(columns, STAGES):
        with column:
            if st.button(f"{number}  {label}", key=f"header_stage_{stage}", use_container_width=True,
                         type="primary" if stage == active_stage else "secondary"):
                st.session_state["active_workspace_stage"] = stage
                st.rerun()
    st.markdown('<hr class="va-rule">', unsafe_allow_html=True)


def render_workspace_sidebar() -> tuple[int, bool, bool]:
    years, show_trade_lines, show_rr_labels = 2, False, False
    with st.sidebar:
        st.markdown('<div class="va-brand">Vector<b>AlgoAI</b></div><div class="va-brand-sub">Research workspace</div>', unsafe_allow_html=True)
        name = st.session_state.get("current_strategy_name") or "Untitled research"
        state = "Evidence available" if st.session_state.get("bt_result") else ("Blueprint ready" if st.session_state.get("blueprint_schema") else "Draft")
        st.markdown('<div class="va-side-label">Current research</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="va-research-card"><div class="va-research-name">{name}</div><div class="va-research-meta">{state}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="va-side-label">Research steps</div>', unsafe_allow_html=True)
        active = st.session_state.get("active_workspace_stage", "thesis")
        for stage, number, label in STAGES:
            if st.button(f"{number}  {label}", key=f"sidebar_stage_{stage}", use_container_width=True, type="primary" if stage == active else "secondary"):
                st.session_state["active_workspace_stage"] = stage
                st.rerun()
        if active == "evidence":
            st.markdown('<div class="va-side-label">Evidence settings</div>', unsafe_allow_html=True)
            years = st.slider("History", 1, 15, 2, format="%d years")
            with st.expander("Chart options"):
                show_trade_lines = st.checkbox("Trade paths")
                show_rr_labels = st.checkbox("R labels")
        else:
            st.markdown('<div class="va-side-label">Guidance</div>', unsafe_allow_html=True)
            hints = {
                "thesis": "Describe the rules in your own words. You will approve the interpretation before testing.",
                "blueprint": "A test only means something when every important assumption is clear.",
                "diagnosis": "Find one structural weakness before changing any strategy rule.",
                "readiness": "This is a risk decision based on evidence, never a performance promise.",
            }
            st.caption(hints.get(active, "Run evidence after approving the blueprint."))
    return years, show_trade_lines, show_rr_labels
