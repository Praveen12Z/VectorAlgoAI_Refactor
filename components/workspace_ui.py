"""UI primitives for the VectorAlgoAI strategy research workspace."""
from __future__ import annotations

from html import escape
import streamlit as st


STAGES = (
    ("thesis", "01", "Thesis", "✦"),
    ("blueprint", "02", "Blueprint", "◇"),
    ("evidence", "03", "Evidence", "◫"),
    ("diagnosis", "04", "Diagnosis", "⌁"),
    ("readiness", "05", "Capital readiness", "↗"),
)

WORKSPACE_ITEMS = (
    ("home", "⌂", "Research home"),
    ("thesis", "＋", "New strategy"),
    ("library", "▦", "Strategy library"),
)


def inject_workspace_styles() -> None:
    """Apply the quiet, permanent-shell product design."""
    st.markdown("""
    <style>
      :root { --bg:#f7f8fa; --sidebar:#ffffff; --surface:#ffffff; --surface-2:#f2f5f9;
        --line:#d9e0e8; --line-soft:#e8edf3; --text:#172033; --muted:#667085;
        --faint:#8993a4; --blue:#2563eb; --blue-strong:#1d4ed8; --blue-bg:#eef4ff; }
      .stApp { background:var(--bg); color:var(--text); }
      /* Keep Streamlit's host controls available, but do not let their header
         create a second, empty product header above the workspace. */
      [data-testid="stHeader"] { background:rgba(255,255,255,.96); border-bottom:1px solid var(--line-soft); height:2rem !important; min-height:2rem !important; }
      [data-testid="stHeader"] [data-testid="stToolbar"] { height:1.8rem !important; min-height:1.8rem !important; }
      [data-testid="stSidebar"] { background:var(--sidebar); border-right:1px solid var(--line); min-width:220px; }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding:1rem .72rem 1rem; display:flex; flex-direction:column; min-height:100%; }
      [data-testid="stSidebar"] .stButton { margin:.08rem 0; }
      [data-testid="stMainBlockContainer"], .block-container { max-width:1180px; padding:.35rem 2.15rem 4rem !important; }
      h1,h2,h3 { color:var(--text); letter-spacing:-.035em; }
      .va-brand-wrap { display:flex; align-items:center; gap:.68rem; padding:.12rem .55rem 1.35rem; }
      .va-mark { width:30px; height:30px; display:grid; place-items:center; border:1px solid #b7cdf8; color:var(--blue); border-radius:8px; background:var(--blue-bg); font-size:1rem; }
      .va-brand { font-size:.92rem; font-weight:760; color:var(--text); letter-spacing:-.025em; }
      .va-brand-sub { color:var(--faint); font-size:.67rem; margin-top:.06rem; }
      .va-side-label { color:var(--faint); font-size:.64rem; font-weight:760; letter-spacing:.12em; text-transform:uppercase; margin:1.35rem .58rem .43rem; }
      .va-side-separator { border-top:1px solid var(--line-soft); margin:1.28rem .55rem 0; }
      .va-research-card { background:#f8fafc; border:1px solid var(--line); border-radius:8px; padding:.68rem .75rem; margin:0 .5rem .35rem; }
      .va-research-name { color:var(--text); font-size:.76rem; font-weight:650; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .va-research-meta { color:var(--faint); font-size:.68rem; margin-top:.22rem; }
      [class*="st-key-nav_"] button { border:0; background:transparent; text-align:left; box-shadow:none; color:#475467; min-height:2.85rem; padding:.34rem .58rem; font-size:.80rem; font-weight:590; border-radius:8px; }
      [class*="st-key-nav_"] button:hover { background:#f3f6fa; color:var(--text); }
      [class*="st-key-nav_"] button[kind="primary"] { background:var(--blue-bg); color:#174ea6; outline:1px solid #c6d8fb; }
      /* A consistent icon tile makes the permanent navigation scannable,
         without turning it into a colourful trading dashboard. */
      [class*="st-key-nav_"] button::before { display:inline-grid !important; place-items:center; flex:0 0 2rem; width:2rem !important; height:2rem !important; margin-right:.72rem; border:1px solid #bfd0e6; border-radius:8px; color:#31577f; background:#f7fafe; font-size:1.12rem !important; font-weight:700; line-height:1; vertical-align:-.25rem; }
      .st-key-nav_workspace_home button::before { content:"⌂"; }
      .st-key-nav_workspace_thesis button::before { content:"+"; }
      .st-key-nav_workspace_library button::before { content:"▦"; }
      .st-key-nav_stage_thesis button::before { content:"✦"; }
      .st-key-nav_stage_blueprint button::before { content:"◇"; }
      .st-key-nav_stage_evidence button::before { content:"◫"; }
      .st-key-nav_stage_diagnosis button::before { content:"⌁"; }
      .st-key-nav_stage_readiness button::before { content:"↗"; }
      .st-key-nav_settings button::before { content:"⚙"; }
      [class*="st-key-nav_"] button[kind="primary"]::before { background:#dbe8ff; border-color:#8eb2f0; color:#174ea6; }
      .va-topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; min-height:2.55rem; padding:0; border-bottom:1px solid var(--line); }
      .va-crumb { color:var(--muted); font-size:.78rem; } .va-crumb b { color:var(--text); font-weight:650; }
      .va-top-status { color:#475467; background:#fff; border:1px solid var(--line); border-radius:999px; padding:.22rem .55rem; font-size:.64rem; white-space:nowrap; }
      .va-top-status i { display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--blue); margin-right:.36rem; vertical-align:1px; }
      .va-page-kicker { color:var(--muted); font-size:.7rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; margin-top:1.45rem; }
      .va-title { font-size:1.72rem; font-weight:650; line-height:1.13; letter-spacing:-.04em; margin:.34rem 0 .35rem; }
      .va-subtitle { color:var(--muted); font-size:.91rem; max-width:720px; line-height:1.55; margin:0 0 1.35rem; }
      .va-workflow { display:flex; align-items:center; gap:0; margin:1.05rem 0 1.8rem; overflow-x:auto; }
      .va-step { display:flex; align-items:center; color:var(--faint); font-size:.72rem; white-space:nowrap; }
      .va-step-dot { display:grid; place-items:center; width:22px; height:22px; border:1px solid #344156; border-radius:50%; margin-right:.38rem; font-size:.62rem; font-weight:700; }
      .va-step.active { color:#e6efff; } .va-step.active .va-step-dot { border-color:var(--blue); background:var(--blue-bg); color:#cfe1ff; }
      .va-step.done { color:#aebfd4; } .va-step.done .va-step-dot { border-color:#496f9e; color:#afd0ff; }
      .va-step-line { width:34px; height:1px; background:#2b3647; margin:0 .58rem; }
      .va-step-line.done { background:#496f9e; }
      .va-workflow-row { margin:0 0 .1rem; height:0; }
      [class*="st-key-workflow_"] { margin-top:-.18rem !important; }
      [class*="st-key-workflow_"] button { min-height:1.7rem !important; height:1.7rem !important; padding:0 .18rem !important; border:0 !important; border-bottom:2px solid var(--line) !important; border-radius:0 !important; background:transparent !important; color:var(--faint) !important; font-size:.69rem !important; text-align:center; box-shadow:none !important; }
      [class*="st-key-workflow_"] button:hover { background:transparent !important; color:var(--text) !important; border-bottom-color:#9db8e8 !important; }
      [class*="st-key-workflow_"] button[kind="primary"] { background:transparent !important; color:#174ea6 !important; border-bottom-color:var(--blue) !important; }
      .va-card { background:var(--surface); border:1px solid var(--line); border-radius:10px; padding:1rem; min-height:104px; box-shadow:0 1px 2px rgba(16,24,40,.025); }
      .va-card-title { color:var(--faint); font-size:.66rem; font-weight:760; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.48rem; }
      .va-card-value { color:var(--text); font-size:.88rem; line-height:1.5; font-weight:560; }
      .va-section-title { color:var(--text); font-size:1.06rem; font-weight:700; margin:2.1rem 0 .22rem; letter-spacing:-.02em; }
      .va-section-copy { color:var(--muted); font-size:.86rem; line-height:1.5; margin-bottom:1rem; }
      .va-evidence-banner { background:#f7faff; border:1px solid #cfdcf3; border-left:3px solid var(--blue-strong); border-radius:8px; padding:1rem 1.1rem; margin:.8rem 0 1.35rem; }
      .va-evidence-kicker { color:var(--blue); font-size:.66rem; font-weight:760; letter-spacing:.1em; text-transform:uppercase; }
      .va-evidence-title { color:var(--text); font-size:.98rem; font-weight:690; margin:.24rem 0; } .va-evidence-meta { color:var(--muted); font-size:.8rem; }
      .va-status { display:inline-block; background:var(--blue-bg); border:1px solid #c6d8fb; color:#174ea6; padding:.23rem .52rem; border-radius:999px; font-size:.68rem; font-weight:700; }
      div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line-soft); border-radius:9px; padding:.82rem .88rem; }
      div[data-testid="stMetricLabel"] { color:var(--muted); font-size:.7rem; } div[data-testid="stMetricValue"] { color:var(--text); font-size:1.22rem; }
      .stButton > button { min-height:2.35rem; border-radius:7px; font-weight:650; border-color:#cfd7e3; background:#fff; color:#344054; }
      .stButton > button:hover { border-color:#8eb2f0; color:#174ea6; background:#f7faff; }
      .stButton > button[kind="primary"] { background:var(--blue); border-color:var(--blue); color:white; }.stButton > button[kind="primary"]:hover { background:var(--blue-strong); }
      [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background:#fff !important; border-color:#cfd7e3 !important; color:var(--text) !important; border-radius:7px !important; }
      [data-testid="stTextArea"] textarea::placeholder, [data-testid="stTextInput"] input::placeholder { color:#98a2b3 !important; opacity:1; }
      [data-testid="stSelectbox"] svg { fill:#667085 !important; }
      [data-testid="stWidgetLabel"] p, .stMarkdown p, label { color:var(--muted); }
      .stTabs [data-baseweb="tab-list"] { gap:1.2rem; border-bottom:1px solid var(--line); }.stTabs [data-baseweb="tab"] { color:var(--muted); padding:.55rem .1rem; }.stTabs [aria-selected="true"] { color:var(--text); border-bottom-color:var(--blue) !important; }
      .stDataFrame { border:1px solid var(--line-soft); border-radius:8px; overflow:hidden; }
    </style>
    """, unsafe_allow_html=True)


def _set_stage(stage: str) -> None:
    st.session_state["active_workspace_stage"] = stage
    st.session_state["active_workspace_view"] = stage


def render_workspace_header(active_stage: str = "thesis") -> None:
    name = escape(st.session_state.get("current_strategy_name") or "Untitled research")
    state = "Evidence available" if st.session_state.get("bt_result") else ("Blueprint ready" if st.session_state.get("blueprint_schema") else "Draft")
    stage_label = next((label for key, _, label, _ in STAGES if key == active_stage), "Research")
    st.markdown(
        f'<div class="va-topbar"><div class="va-crumb">Research / <b>{name}</b> / {stage_label}</div>'
        f'<div class="va-top-status"><i></i>{state}</div></div>',
        unsafe_allow_html=True,
    )
    # This is deliberately a compact progress control, not a second navigation bar.
    st.markdown('<div class="va-workflow-row">', unsafe_allow_html=True)
    workflow = st.columns(len(STAGES), gap="small")
    for column, (key, number, label, _) in zip(workflow, STAGES):
        with column:
            if st.button(f"{number}  {label}", key=f"workflow_{key}", use_container_width=True,
                         type="primary" if key == active_stage else "secondary"):
                _set_stage(key)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)


def render_workspace_sidebar() -> tuple[int, bool, bool]:
    years, show_trade_lines, show_rr_labels = 2, False, False
    with st.sidebar:
        st.markdown('<div class="va-brand-wrap"><div class="va-mark">◈</div><div><div class="va-brand">VectorAlgoAI</div><div class="va-brand-sub">Strategy research workspace</div></div></div>', unsafe_allow_html=True)
        active = st.session_state.get("active_workspace_stage", "thesis")
        st.markdown('<div class="va-side-label">Workspace</div>', unsafe_allow_html=True)
        for destination, icon, label in WORKSPACE_ITEMS:
            target = "thesis" if destination == "thesis" else destination
            if st.button(label, key=f"nav_workspace_{destination}", use_container_width=True, type="primary" if active == target else "secondary"):
                _set_stage(target)
                st.rerun()
        st.markdown('<div class="va-side-separator"></div><div class="va-side-label">Current research</div>', unsafe_allow_html=True)
        name = escape(st.session_state.get("current_strategy_name") or "Untitled research")
        state = "Evidence available" if st.session_state.get("bt_result") else ("Blueprint ready" if st.session_state.get("blueprint_schema") else "Draft")
        st.markdown(f'<div class="va-research-card"><div class="va-research-name">{name}</div><div class="va-research-meta">{state}</div></div>', unsafe_allow_html=True)
        for stage, number, label, icon in STAGES:
            if st.button(label, key=f"nav_stage_{stage}", use_container_width=True, type="primary" if stage == active else "secondary"):
                _set_stage(stage)
                st.rerun()
        st.markdown('<div class="va-side-separator"></div><div class="va-side-label">Account</div>', unsafe_allow_html=True)
        if st.button("Settings", key="nav_settings", use_container_width=True, type="primary" if active == "settings" else "secondary"):
            _set_stage("settings")
            st.rerun()
        if active == "evidence":
            st.markdown('<div class="va-side-label">Evidence settings</div>', unsafe_allow_html=True)
            years = st.slider("History", 1, 15, 2, format="%d years")
            with st.expander("Chart options"):
                show_trade_lines = st.checkbox("Trade paths")
                show_rr_labels = st.checkbox("R labels")
    return years, show_trade_lines, show_rr_labels
