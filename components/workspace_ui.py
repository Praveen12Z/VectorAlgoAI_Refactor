"""UI primitives for the VectorAlgoAI strategy research workspace."""
from __future__ import annotations

from html import escape
import streamlit as st


STAGES = (
    ("thesis", "01", "Strategy Brief", "✦"),
    ("blueprint", "02", "Rule Blueprint", "◇"),
    ("evidence", "03", "Backtest Results", "◫"),
    ("diagnosis", "04", "Strategy Diagnosis", "⌁"),
    ("readiness", "05", "Deployment Readiness", "↗"),
)

WORKSPACE_ITEMS = (
    ("thesis", "✦", "Strategy Lab"),
    ("library", "▦", "Strategy Library"),
    ("journal", "▤", "Trade Journal"),
)

INTELLIGENCE_ITEMS = (
    ("regimes", "◎", "Market Regimes"),
    ("experiments", "⌬", "Experiments"),
)


def inject_workspace_styles() -> None:
    """Apply the quiet, permanent-shell product design."""
    st.markdown("""
    <style>
      :root { --bg:#f4f7fb; --sidebar:#f9fbfe; --surface:#fff; --surface-2:#edf3f8;
        --line:#dbe4ee; --line-soft:#e9eff5; --text:#10233f; --muted:#5c6f86;
        --faint:#8a9aaf; --blue:#2563eb; --blue-strong:#1d4ed8; --blue-bg:#eaf1ff;
        --teal:#0f9f9a; --teal-strong:#0b7f7b; --teal-bg:#e7f8f6;
        --green:#168568; --green-bg:#eaf8f2; --amber:#b7791f; --amber-bg:#fff7e6;
        --red:#c24156; --red-bg:#fff0f2; }
      .stApp { background:linear-gradient(135deg,#f8fbff 0%,var(--bg) 46%,#f2f8f8 100%); color:var(--text); }
      /* Keep Streamlit's host controls available, but do not let their header
         create a second, empty product header above the workspace. */
      [data-testid="stHeader"] { background:transparent; height:0 !important; min-height:0 !important; }
      [data-testid="stHeader"] [data-testid="stToolbar"] { top:.45rem; right:.55rem; }
      [data-testid="stSidebar"] { background:linear-gradient(180deg,#fbfdff 0%,var(--sidebar) 58%,#f3f8fa 100%); border-right:1px solid var(--line); min-width:190px; max-width:190px; }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding:.85rem .65rem 1rem; display:flex; flex-direction:column; min-height:100%; }
      [data-testid="stSidebar"] .stButton { margin:.08rem 0; }
      [data-testid="stMainBlockContainer"], .block-container { max-width:1132px; padding:0 26px 4rem !important; }
      h1,h2,h3 { color:var(--text); letter-spacing:-.035em; }
      .va-brand-wrap { display:flex; align-items:center; gap:.6rem; padding:.15rem .5rem 1.65rem; }
      .va-mark { width:29px; height:29px; display:grid; place-items:center; color:#fff; border-radius:8px; background:linear-gradient(135deg,var(--blue),var(--teal)); box-shadow:0 5px 14px rgba(37,99,235,.22); font-size:.9rem; }
      .va-brand { font-size:.91rem; font-weight:720; color:var(--text); letter-spacing:-.025em; }
      .va-brand b { color:var(--blue); font-weight:760; }
      .va-brand-sub { display:none; }
      .va-side-label { color:var(--faint); font-size:.59rem; font-weight:720; letter-spacing:.1em; text-transform:uppercase; margin:1rem .58rem .36rem; }
      .va-side-separator { border-top:1px solid var(--line-soft); margin:1.28rem .55rem 0; }
      .va-research-card { background:#f8fafc; border:1px solid var(--line); border-radius:8px; padding:.68rem .75rem; margin:0 .5rem .35rem; }
      .va-research-name { color:var(--text); font-size:.76rem; font-weight:650; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .va-research-meta { color:var(--faint); font-size:.68rem; margin-top:.22rem; }
      [class*="st-key-nav_"] button { border:0 !important; background:transparent !important; text-align:left; box-shadow:none !important; color:#475467 !important; min-height:2.25rem; padding:.28rem .5rem; font-size:.75rem; font-weight:540; border-radius:7px; }
      [class*="st-key-nav_"] button:hover { background:#edf4fb !important; color:var(--text) !important; }
      [class*="st-key-nav_"] button[kind="primary"] { background:linear-gradient(90deg,var(--blue-bg),#edf8fa) !important; color:#1e4fae !important; box-shadow:inset 3px 0 0 var(--blue) !important; outline:0; }
      /* A consistent icon tile makes the permanent navigation scannable,
         without turning it into a colourful trading dashboard. */
      [class*="st-key-nav_"] button::before { display:inline-grid !important; place-items:center; flex:0 0 1.5rem; width:1.5rem !important; height:1.5rem !important; margin-right:.42rem; border:0; border-radius:6px; color:#667085; background:transparent; font-size:.9rem !important; font-weight:650; line-height:1; vertical-align:-.18rem; }
      .st-key-nav_workspace_home button::before { content:"⌂"; }
      .st-key-nav_workspace_thesis button::before { content:"+"; }
      .st-key-nav_workspace_library button::before { content:"▦"; }
      .st-key-nav_workspace_journal button::before { content:"▤"; }
      .st-key-nav_intelligence_regimes button::before { content:"◎"; }
      .st-key-nav_intelligence_experiments button::before { content:"⌬"; }
      .st-key-nav_stage_thesis button::before { content:"✦"; }
      .st-key-nav_stage_blueprint button::before { content:"◇"; }
      .st-key-nav_stage_evidence button::before { content:"◫"; }
      .st-key-nav_stage_diagnosis button::before { content:"⌁"; }
      .st-key-nav_stage_readiness button::before { content:"↗"; }
      .st-key-nav_settings button::before { content:"⚙"; }
      [class*="st-key-nav_"] button[kind="primary"]::before { background:linear-gradient(135deg,#dce8ff,#d9f3f1); color:var(--teal-strong); }
      .va-topbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; min-height:54px; padding:0; border-bottom:1px solid var(--line); }
      .va-crumb { color:var(--muted); font-size:.78rem; } .va-crumb b { color:var(--text); font-weight:650; }
      .va-top-actions { display:flex; align-items:center; gap:.55rem; }
      .va-draft { color:#475467; background:#f2f4f7; border-radius:999px; padding:.2rem .5rem; font-size:.63rem; margin-left:.35rem; }
      .va-top-status { color:#667085; background:transparent; border:0; padding:.22rem; font-size:.66rem; white-space:nowrap; }
      .va-top-status i { display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--teal); box-shadow:0 0 0 3px var(--teal-bg); margin-right:.42rem; vertical-align:1px; }
      .va-page-kicker { color:var(--muted); font-size:.65rem; font-weight:680; letter-spacing:.1em; text-transform:uppercase; margin-top:1.45rem; }
      .va-title { font-size:1.72rem; font-weight:570; line-height:1.13; letter-spacing:-.04em; margin:.34rem 0 .35rem; }
      .va-subtitle { color:var(--muted); font-size:.91rem; max-width:720px; line-height:1.55; margin:0 0 1.35rem; }
      .va-workflow { display:flex; align-items:center; gap:0; margin:1.05rem 0 1.8rem; overflow-x:auto; }
      .va-step { display:flex; align-items:center; color:var(--faint); font-size:.72rem; white-space:nowrap; }
      .va-step-dot { display:grid; place-items:center; width:22px; height:22px; border:1px solid var(--line); border-radius:50%; margin-right:.38rem; font-size:.62rem; font-weight:700; }
      .va-step.active { color:var(--blue); } .va-step.active .va-step-dot { border-color:var(--blue); background:var(--blue-bg); color:var(--blue); }
      .va-step.done { color:var(--teal-strong); } .va-step.done .va-step-dot { border-color:#72c9c3; background:var(--teal-bg); color:var(--teal-strong); }
      .va-step-line { width:34px; height:1px; background:var(--line); margin:0 .58rem; }
      .va-step-line.done { background:#72c9c3; }
      .va-workflow-row { margin:0 0 .1rem; height:0; }
      [class*="st-key-workflow_"] { margin-top:-.18rem !important; }
      [class*="st-key-workflow_"] button { min-height:2rem !important; height:2rem !important; padding:0 .18rem !important; border:0 !important; border-bottom:1px solid var(--line) !important; border-radius:0 !important; background:transparent !important; color:var(--faint) !important; font-size:.67rem !important; text-align:center; box-shadow:none !important; white-space:nowrap; }
      [class*="st-key-workflow_"] button:hover { background:transparent !important; color:var(--text) !important; border-bottom-color:#9db8e8 !important; }
      [class*="st-key-workflow_"] button[kind="primary"] { background:transparent !important; color:#174ea6 !important; border-bottom-color:var(--blue) !important; }
      .va-card { background:linear-gradient(180deg,#fff 0%,#fbfdff 100%); border:1px solid var(--line); border-radius:10px; padding:1rem; min-height:104px; box-shadow:0 5px 18px rgba(34,66,105,.045); }
      .va-composer { background:linear-gradient(180deg,#fff 0%,#fbfdff 100%); border:1px solid #cfddeb; border-top:3px solid var(--blue); border-radius:10px; padding:1.15rem; box-shadow:0 8px 24px rgba(37,99,235,.07); }
      .va-composer-head { display:flex; gap:.7rem; align-items:flex-start; margin-bottom:.8rem; }
      .va-ai-orb { display:grid; place-items:center; flex:0 0 34px; width:34px; height:34px; border-radius:9px; background:linear-gradient(135deg,var(--blue-bg),var(--teal-bg)); color:var(--teal-strong); box-shadow:inset 0 0 0 1px rgba(15,159,154,.15); }
      .va-panel-title { color:var(--text); font-size:.92rem; font-weight:620; margin-bottom:.15rem; }
      .va-panel-copy { color:var(--muted); font-size:.73rem; line-height:1.45; }
      .va-chip { display:inline-block; border:1px solid #cfe1ea; background:#f1f8fa; color:#31657a; padding:.18rem .46rem; border-radius:999px; font-size:.65rem; margin:.35rem .28rem 0 0; }
      .va-card-title { color:var(--faint); font-size:.66rem; font-weight:760; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.48rem; }
      .va-card-value { color:var(--text); font-size:.88rem; line-height:1.5; font-weight:560; }
      .va-section-title { color:var(--text); font-size:1.06rem; font-weight:700; margin:2.1rem 0 .22rem; letter-spacing:-.02em; }
      .va-section-copy { color:var(--muted); font-size:.86rem; line-height:1.5; margin-bottom:1rem; }
      .va-evidence-banner { background:linear-gradient(110deg,var(--blue-bg),#f7fbff 54%,var(--teal-bg)); border:1px solid #c8dbea; border-left:3px solid var(--teal); border-radius:8px; padding:1rem 1.1rem; margin:.8rem 0 1.35rem; }
      .va-evidence-kicker { color:var(--teal-strong); font-size:.66rem; font-weight:760; letter-spacing:.1em; text-transform:uppercase; }
      .va-evidence-title { color:var(--text); font-size:.98rem; font-weight:690; margin:.24rem 0; } .va-evidence-meta { color:var(--muted); font-size:.8rem; }
      .va-status { display:inline-block; background:linear-gradient(90deg,var(--blue-bg),var(--teal-bg)); border:1px solid #badbdc; color:var(--teal-strong); padding:.23rem .52rem; border-radius:999px; font-size:.68rem; font-weight:700; }
      div[data-testid="stMetric"] { background:linear-gradient(180deg,#fff,#f8fbff); border:1px solid var(--line-soft); border-top:2px solid #93b7ee; border-radius:9px; padding:.82rem .88rem; box-shadow:0 4px 14px rgba(34,66,105,.035); }
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
      [data-testid="stAlert"] { border-radius:9px; border-width:1px; }
      [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p { color:inherit; }
      @media(max-width:700px){[data-testid="stSidebar"]{min-width:0;max-width:none}[data-testid="stMainBlockContainer"],.block-container{padding:0 12px 3rem!important}.va-topbar{min-height:48px}.va-draft{display:none}[class*="st-key-workflow_"] button{font-size:0!important}[class*="st-key-workflow_"] button::first-letter{font-size:.7rem}}
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
        f'<div class="va-topbar"><div class="va-crumb"><span>Strategy Lab</span> &nbsp;›&nbsp; <b>{name}</b><span class="va-draft">Draft 04</span></div>'
        f'<div class="va-top-actions"><div class="va-top-status"><i></i>{state}</div><div class="va-top-status">↶ Versions</div></div></div>',
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
        st.markdown('<div class="va-brand-wrap"><div class="va-mark">⌁</div><div><div class="va-brand">VectorAlgo<b>AI</b></div><div class="va-brand-sub">Strategy research workspace</div></div></div>', unsafe_allow_html=True)
        active = st.session_state.get("active_workspace_stage", "thesis")
        st.markdown('<div class="va-side-label">Research</div>', unsafe_allow_html=True)
        for destination, icon, label in WORKSPACE_ITEMS:
            target = "thesis" if destination == "thesis" else destination
            if st.button(label, key=f"nav_workspace_{destination}", use_container_width=True, type="primary" if active == target else "secondary"):
                _set_stage(target)
                st.rerun()
        st.markdown('<div class="va-side-label">Intelligence</div>', unsafe_allow_html=True)
        for destination, icon, label in INTELLIGENCE_ITEMS:
            if st.button(label, key=f"nav_intelligence_{destination}", use_container_width=True):
                st.session_state["active_workspace_view"] = destination
                st.rerun()
        st.markdown('<div style="height:8rem"></div><div class="va-side-separator"></div>', unsafe_allow_html=True)
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
