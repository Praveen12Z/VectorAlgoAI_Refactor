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
      :root { --bg:#0a0e15; --sidebar:#0d121c; --surface:#121925; --surface-2:#171f2c;
        --line:#273244; --line-soft:#1d2736; --text:#f2f5fa; --muted:#92a0b3;
        --faint:#647287; --blue:#73a9ff; --blue-strong:#4388ef; --blue-bg:#172b4a; }
      .stApp { background:var(--bg); color:var(--text); }
      /* Keep Streamlit's host controls available, but do not let their header
         create a second, empty product header above the workspace. */
      [data-testid="stHeader"] { background:rgba(10,14,21,.82); border-bottom:1px solid var(--line-soft); height:1.8rem !important; min-height:1.8rem !important; }
      [data-testid="stHeader"] [data-testid="stToolbar"] { height:1.8rem !important; min-height:1.8rem !important; }
      [data-testid="stSidebar"] { background:var(--sidebar); border-right:1px solid var(--line-soft); min-width:226px; }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding:1.25rem .72rem 1rem; display:flex; flex-direction:column; min-height:100%; }
      [data-testid="stSidebar"] .stButton { margin:.08rem 0; }
      [data-testid="stMainBlockContainer"], .block-container { max-width:1390px; padding:.08rem 2.4rem 4rem !important; }
      h1,h2,h3 { color:var(--text); letter-spacing:-.035em; }
      .va-brand-wrap { display:flex; align-items:center; gap:.68rem; padding:.16rem .55rem 1.25rem; }
      .va-mark { width:27px; height:27px; display:grid; place-items:center; border:1px solid #416b9f; color:#b9d2ff; border-radius:8px; background:#11223a; font-size:.95rem; }
      .va-brand { font-size:.92rem; font-weight:760; color:#f6f8fc; letter-spacing:-.025em; }
      .va-brand-sub { color:var(--faint); font-size:.67rem; margin-top:.06rem; }
      .va-side-label { color:var(--faint); font-size:.64rem; font-weight:760; letter-spacing:.12em; text-transform:uppercase; margin:1.35rem .58rem .43rem; }
      .va-side-separator { border-top:1px solid var(--line-soft); margin:1.28rem .55rem 0; }
      .va-research-card { background:#101722; border:1px solid var(--line-soft); border-radius:8px; padding:.68rem .75rem; margin:0 .5rem .35rem; }
      .va-research-name { color:#dfe7f2; font-size:.76rem; font-weight:650; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .va-research-meta { color:var(--faint); font-size:.68rem; margin-top:.22rem; }
      [class*="st-key-nav_"] button { border:0; background:transparent; text-align:left; box-shadow:none; color:#9aa8ba; min-height:3.05rem; padding:.38rem .58rem; font-size:.80rem; font-weight:590; border-radius:8px; }
      [class*="st-key-nav_"] button::first-letter { color:#b7d3ff; }
      [class*="st-key-nav_"] button:hover { background:#131c29; color:#e9f0fa; }
      [class*="st-key-nav_"] button[kind="primary"] { background:var(--blue-bg); color:#eef5ff; outline:1px solid #294f7b; }
      /* A consistent icon tile makes the permanent navigation scannable,
         without turning it into a colourful trading dashboard. */
      [class*="st-key-nav_"] button::before { display:inline-grid !important; place-items:center; flex:0 0 2rem; width:2rem !important; height:2rem !important; margin-right:.72rem; border:1px solid #4775aa; border-radius:8px; color:#d8e7ff; background:#11243a; font-size:1.12rem !important; font-weight:700; line-height:1; vertical-align:-.25rem; box-shadow:inset 0 0 0 1px rgba(115,169,255,.06); }
      .st-key-nav_workspace_home button::before { content:"⌂"; }
      .st-key-nav_workspace_thesis button::before { content:"+"; }
      .st-key-nav_workspace_library button::before { content:"▦"; }
      .st-key-nav_stage_thesis button::before { content:"✦"; }
      .st-key-nav_stage_blueprint button::before { content:"◇"; }
      .st-key-nav_stage_evidence button::before { content:"◫"; }
      .st-key-nav_stage_diagnosis button::before { content:"⌁"; }
      .st-key-nav_stage_readiness button::before { content:"↗"; }
      .st-key-nav_settings button::before { content:"⚙"; }
      [class*="st-key-nav_"] button[kind="primary"]::before { background:#1c3c65; border-color:#5386bf; color:#e4f0ff; }
      .va-topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; min-height:1.5rem; padding:0 0 .18rem; border-bottom:1px solid var(--line-soft); }
      .va-crumb { color:var(--muted); font-size:.78rem; } .va-crumb b { color:var(--text); font-weight:650; }
      .va-top-status { color:#b9c7d9; background:#101925; border:1px solid #25374c; border-radius:999px; padding:.14rem .5rem; font-size:.64rem; white-space:nowrap; }
      .va-top-status i { display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--blue); margin-right:.36rem; vertical-align:1px; }
      .va-page-kicker { color:var(--blue); font-size:.67rem; font-weight:760; letter-spacing:.12em; text-transform:uppercase; margin-top:1.25rem; }
      .va-title { font-size:1.8rem; font-weight:730; line-height:1.13; letter-spacing:-.048em; margin:.34rem 0 .35rem; }
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
      [class*="st-key-workflow_"] button { min-height:1.55rem !important; height:1.55rem !important; padding:0 .18rem !important; border:0 !important; border-bottom:2px solid #2b3647 !important; border-radius:0 !important; background:transparent !important; color:var(--faint) !important; font-size:.67rem !important; text-align:center; box-shadow:none !important; }
      [class*="st-key-workflow_"] button:hover { background:transparent !important; color:#dce8f7 !important; border-bottom-color:#577ba7 !important; }
      [class*="st-key-workflow_"] button[kind="primary"] { background:transparent !important; color:#e9f1fd !important; border-bottom-color:var(--blue) !important; }
      .va-card { background:var(--surface); border:1px solid var(--line-soft); border-radius:9px; padding:1rem; min-height:104px; }
      .va-card-title { color:var(--faint); font-size:.66rem; font-weight:760; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.48rem; }
      .va-card-value { color:#e8edf5; font-size:.88rem; line-height:1.5; font-weight:560; }
      .va-section-title { color:var(--text); font-size:1.06rem; font-weight:700; margin:2.1rem 0 .22rem; letter-spacing:-.02em; }
      .va-section-copy { color:var(--muted); font-size:.86rem; line-height:1.5; margin-bottom:1rem; }
      .va-evidence-banner { background:#101925; border:1px solid #25374c; border-left:3px solid var(--blue-strong); border-radius:8px; padding:1rem 1.1rem; margin:.8rem 0 1.35rem; }
      .va-evidence-kicker { color:var(--blue); font-size:.66rem; font-weight:760; letter-spacing:.1em; text-transform:uppercase; }
      .va-evidence-title { color:var(--text); font-size:.98rem; font-weight:690; margin:.24rem 0; } .va-evidence-meta { color:var(--muted); font-size:.8rem; }
      .va-status { display:inline-block; background:var(--blue-bg); border:1px solid #2d4e75; color:#cbdfff; padding:.23rem .52rem; border-radius:999px; font-size:.68rem; font-weight:700; }
      div[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line-soft); border-radius:9px; padding:.82rem .88rem; }
      div[data-testid="stMetricLabel"] { color:var(--muted); font-size:.7rem; } div[data-testid="stMetricValue"] { color:var(--text); font-size:1.22rem; }
      .stButton > button { min-height:2.35rem; border-radius:7px; font-weight:650; border-color:#334256; background:transparent; color:#c9d3df; }
      .stButton > button:hover { border-color:#6383aa; color:#f6f8fb; background:#141e2b; }
      .stButton > button[kind="primary"] { background:#2f6dbd; border-color:#4381d2; color:white; }.stButton > button[kind="primary"]:hover { background:#3978ca; }
      [data-testid="stTextArea"] textarea, [data-testid="stTextInput"] input, [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background:#0e151f !important; border-color:#334154 !important; color:var(--text) !important; border-radius:7px !important; }
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
